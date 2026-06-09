import uuid

from sqlalchemy.orm import selectinload

from src.extensions.database import db
from src.models.models import Tag, UserTagInterest


def find_tag_by_id(tag_id: int) -> Tag | None:
    return db.session.get(Tag, tag_id)


def list_interests(user_id: uuid.UUID) -> list[UserTagInterest]:
    result = db.session.execute(
        db.select(UserTagInterest)
        .where(UserTagInterest.user_id == user_id)
        .options(selectinload(UserTagInterest.tag))
        .order_by(UserTagInterest.weight.desc())
    )
    return list(result.scalars())


def replace_interests(user_id: uuid.UUID, interesses: list[dict]) -> list[UserTagInterest]:
    db.session.execute(
        db.delete(UserTagInterest).where(UserTagInterest.user_id == user_id)
    )

    for item in interesses:
        db.session.add(UserTagInterest(
            user_id=user_id,
            tag_id=item["tag_id"],
            weight=item["weight"],
        ))

    db.session.commit()

    # Recarrega com relacionamento tag para evitar N+1 na serialização
    result = db.session.execute(
        db.select(UserTagInterest)
        .where(UserTagInterest.user_id == user_id)
        .options(selectinload(UserTagInterest.tag))
        .order_by(UserTagInterest.weight.desc())
    )
    return list(result.scalars())
