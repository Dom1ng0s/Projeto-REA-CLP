import uuid

from sqlalchemy.orm import selectinload

from src.extensions.database import db
from src.models.models import Tag, UserInterest


def find_tag_by_id(tag_id) -> Tag | None:
    return db.session.get(Tag, tag_id)


def find_tag_by_slug(slug: str) -> Tag | None:
    return db.session.execute(
        db.select(Tag).where(Tag.slug == slug)
    ).scalar_one_or_none()


def list_interests(user_id: uuid.UUID) -> list[UserInterest]:
    result = db.session.execute(
        db.select(UserInterest)
        .where(UserInterest.user_id == user_id)
        .options(selectinload(UserInterest.tag))
        .order_by(UserInterest.weight.desc())
    )
    return list(result.scalars())


def replace_interests(user_id: uuid.UUID, interesses: list[dict]) -> list[UserInterest]:
    db.session.execute(
        db.delete(UserInterest).where(UserInterest.user_id == user_id)
    )

    for item in interesses:
        db.session.add(UserInterest(
            user_id=user_id,
            tag_id=item["tag_id"],
            weight=item["weight"],
        ))

    db.session.commit()

    result = db.session.execute(
        db.select(UserInterest)
        .where(UserInterest.user_id == user_id)
        .options(selectinload(UserInterest.tag))
        .order_by(UserInterest.weight.desc())
    )
    return list(result.scalars())
