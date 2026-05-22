from pathlib import Path
import yaml
from sqlalchemy.orm import Session
from .models import Category, Question, Challenge

CONTENT_PATH = Path(__file__).resolve().parents[1] / "content" / "question-bank.yaml"


def _get_or_create_category(db: Session, item: dict) -> Category:
    category = db.query(Category).filter(Category.slug == item["slug"]).first()
    if category is None:
        category = Category(slug=item["slug"], name=item["name"], description=item.get("description", ""))
        db.add(category)
        db.flush()
    else:
        category.name = item["name"]
        category.description = item.get("description", "")
    return category


def seed_database(db: Session) -> None:
    """Upsert the bundled content pack.

    The original MVP seeded only an empty database. For a production-style learning
    platform, content updates must be repeatable: redeploying the API should add
    new questions/labs and refresh existing seeded items without wiping attempts.
    """
    data = yaml.safe_load(CONTENT_PATH.read_text())

    categories: dict[str, Category] = {}
    for item in data.get("categories", []):
        category = _get_or_create_category(db, item)
        categories[category.slug] = category

    for item in data.get("questions", []):
        category = categories[item["category"]]
        question = db.query(Question).filter(Question.slug == item["slug"]).first()
        values = dict(
            title=item["title"],
            category_id=category.id,
            difficulty=item.get("difficulty", "Intermediate"),
            type=item.get("type", "multiple_choice"),
            prompt=item["prompt"],
            choices=item.get("choices"),
            correct_answer=item.get("correct_answer"),
            explanation=item.get("explanation", ""),
            tags=item.get("tags", []),
        )
        if question is None:
            db.add(Question(slug=item["slug"], **values))
        else:
            for key, value in values.items():
                setattr(question, key, value)

    for item in data.get("challenges", []):
        category = categories[item["category"]]
        challenge = db.query(Challenge).filter(Challenge.slug == item["slug"]).first()
        values = dict(
            title=item["title"],
            category_id=category.id,
            difficulty=item.get("difficulty", "Intermediate"),
            type=item.get("type", "challenge"),
            prompt=item["prompt"],
            starter_files=item.get("starter_files", {}),
            test_rules=item.get("test_rules", []),
            explanation=item.get("explanation", ""),
            tags=item.get("tags", []),
        )
        if challenge is None:
            db.add(Challenge(slug=item["slug"], **values))
        else:
            for key, value in values.items():
                setattr(challenge, key, value)

    db.commit()
