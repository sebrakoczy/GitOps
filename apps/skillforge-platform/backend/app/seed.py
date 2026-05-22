from pathlib import Path
import yaml
from sqlalchemy.orm import Session
from .models import Category, Question, Challenge

CONTENT_PATH = Path(__file__).resolve().parents[1] / "content" / "question-bank.yaml"


def seed_database(db: Session) -> None:
    if db.query(Category).count() > 0:
        return
    data = yaml.safe_load(CONTENT_PATH.read_text())
    categories: dict[str, Category] = {}
    for item in data.get("categories", []):
        category = Category(slug=item["slug"], name=item["name"], description=item.get("description", ""))
        db.add(category)
        db.flush()
        categories[category.slug] = category

    for item in data.get("questions", []):
        category = categories[item["category"]]
        question = Question(
            slug=item["slug"],
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
        db.add(question)

    for item in data.get("challenges", []):
        category = categories[item["category"]]
        challenge = Challenge(
            slug=item["slug"],
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
        db.add(challenge)
    db.commit()
