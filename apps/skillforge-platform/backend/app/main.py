from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from .database import Base, engine, get_db, session_scope
from .grader import grade_challenge, grade_question
from .models import Attempt, Category, Challenge, Question, Submission
from .schemas import AttemptIn, AttemptOut, CategoryOut, ChallengeOut, DashboardOut, QuestionOut, SubmissionIn, SubmissionOut
from .seed import seed_database

app = FastAPI(title="SkillForge Platform API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    with session_scope() as db:
        seed_database(db)

@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/api/categories", response_model=list[CategoryOut])
def categories(db: Session = Depends(get_db)):
    return db.query(Category).order_by(Category.name).all()

@app.get("/api/questions", response_model=list[QuestionOut])
def questions(
    category: str | None = Query(default=None),
    difficulty: str | None = Query(default=None),
    q: str | None = Query(default=None),
    limit: int = Query(default=1000, le=1000),
    db: Session = Depends(get_db),
):
    query = db.query(Question).options(joinedload(Question.category)).join(Category)
    if category:
        query = query.filter(Category.slug == category)
    if difficulty:
        query = query.filter(Question.difficulty == difficulty)
    if q:
        like = f"%{q}%"
        query = query.filter((Question.title.ilike(like)) | (Question.prompt.ilike(like)))
    return query.order_by(Category.name, Question.difficulty, Question.title).limit(limit).all()

@app.get("/api/questions/{question_id}", response_model=QuestionOut)
def question_detail(question_id: int, db: Session = Depends(get_db)):
    question = db.query(Question).options(joinedload(Question.category)).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question

@app.post("/api/attempts", response_model=AttemptOut)
def create_attempt(payload: AttemptIn, db: Session = Depends(get_db)):
    question = db.query(Question).filter(Question.id == payload.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    score, passed, feedback = grade_question(question.type, question.correct_answer, payload.answer, question.explanation)
    attempt = Attempt(question_id=question.id, answer=payload.answer, score=score, passed=passed, feedback=feedback)
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt

@app.get("/api/challenges", response_model=list[ChallengeOut])
def challenges(
    category: str | None = Query(default=None),
    difficulty: str | None = Query(default=None),
    q: str | None = Query(default=None),
    limit: int = Query(default=1000, le=1000),
    db: Session = Depends(get_db),
):
    query = db.query(Challenge).options(joinedload(Challenge.category)).join(Category)
    if category:
        query = query.filter(Category.slug == category)
    if difficulty:
        query = query.filter(Challenge.difficulty == difficulty)
    if q:
        like = f"%{q}%"
        query = query.filter((Challenge.title.ilike(like)) | (Challenge.prompt.ilike(like)))
    return query.order_by(Category.name, Challenge.difficulty, Challenge.title).limit(limit).all()

@app.get("/api/challenges/{challenge_id}", response_model=ChallengeOut)
def challenge_detail(challenge_id: int, db: Session = Depends(get_db)):
    challenge = db.query(Challenge).options(joinedload(Challenge.category)).filter(Challenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return challenge

@app.post("/api/submissions", response_model=SubmissionOut)
def create_submission(payload: SubmissionIn, db: Session = Depends(get_db)):
    challenge = db.query(Challenge).filter(Challenge.id == payload.challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    result = grade_challenge(challenge.test_rules, payload.solution)
    submission = Submission(
        challenge_id=challenge.id,
        solution=payload.solution,
        score=result["score"],
        passed=result["passed"],
        result=result,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission

@app.get("/api/dashboard", response_model=DashboardOut)
def dashboard(db: Session = Depends(get_db)):
    total_questions = db.query(func.count(Question.id)).scalar() or 0
    total_challenges = db.query(func.count(Challenge.id)).scalar() or 0
    attempts = db.query(func.count(Attempt.id)).scalar() or 0
    submissions = db.query(func.count(Submission.id)).scalar() or 0
    avg_attempt = db.query(func.avg(Attempt.score)).scalar() or 0
    avg_submission = db.query(func.avg(Submission.score)).scalar() or 0
    if attempts and submissions:
        avg_score = (float(avg_attempt) + float(avg_submission)) / 2
    elif attempts:
        avg_score = float(avg_attempt)
    elif submissions:
        avg_score = float(avg_submission)
    else:
        avg_score = 0.0

    breakdown = []
    for category in db.query(Category).order_by(Category.name).all():
        question_ids = [q.id for q in db.query(Question.id).filter(Question.category_id == category.id).all()]
        challenge_ids = [c.id for c in db.query(Challenge.id).filter(Challenge.category_id == category.id).all()]
        q_avg = db.query(func.avg(Attempt.score)).filter(Attempt.question_id.in_(question_ids)).scalar() if question_ids else None
        c_avg = db.query(func.avg(Submission.score)).filter(Submission.challenge_id.in_(challenge_ids)).scalar() if challenge_ids else None
        domain_scores = [float(s) for s in [q_avg, c_avg] if s is not None]
        breakdown.append({
            "slug": category.slug,
            "name": category.name,
            "questions": len(question_ids),
            "challenges": len(challenge_ids),
            "score": round(sum(domain_scores) / len(domain_scores), 1) if domain_scores else 0,
        })

    return DashboardOut(
        total_questions=total_questions,
        total_challenges=total_challenges,
        attempts=attempts,
        submissions=submissions,
        average_score=round(avg_score, 1),
        readiness_score=round(avg_score),
        domain_breakdown=breakdown,
    )
