from typing import Any
from pydantic import BaseModel

class CategoryOut(BaseModel):
    id: int
    slug: str
    name: str
    description: str
    class Config:
        from_attributes = True

class QuestionOut(BaseModel):
    id: int
    slug: str
    title: str
    category_id: int
    difficulty: str
    type: str
    prompt: str
    choices: list[Any] | None = None
    explanation: str | None = None
    tags: list[str] | None = None
    category: CategoryOut | None = None
    class Config:
        from_attributes = True

class ChallengeOut(BaseModel):
    id: int
    slug: str
    title: str
    category_id: int
    difficulty: str
    type: str
    prompt: str
    starter_files: dict[str, str] | None = None
    test_rules: list[dict[str, Any]] | None = None
    explanation: str | None = None
    tags: list[str] | None = None
    category: CategoryOut | None = None
    class Config:
        from_attributes = True

class AttemptIn(BaseModel):
    question_id: int
    answer: Any

class AttemptOut(BaseModel):
    id: int
    question_id: int
    answer: Any
    score: int
    passed: bool
    feedback: str
    class Config:
        from_attributes = True

class SubmissionIn(BaseModel):
    challenge_id: int
    solution: str

class SubmissionOut(BaseModel):
    id: int
    challenge_id: int
    score: int
    passed: bool
    result: dict[str, Any] | None = None
    class Config:
        from_attributes = True

class DashboardOut(BaseModel):
    total_questions: int
    total_challenges: int
    attempts: int
    submissions: int
    average_score: float
    readiness_score: int
    domain_breakdown: list[dict[str, Any]]
