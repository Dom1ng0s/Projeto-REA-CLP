import uuid

from sqlalchemy import func

from src.extensions.database import db
from src.models.models import REA, REATag, StatusREAEnum, UserTagInterest


def list_visible(q: str | None, page: int, per_page: int):
    query = db.select(REA).where(REA.status == StatusREAEnum.ativo)

    if q:
        term = f"%{q}%"
        query = query.where(REA.title.ilike(term) | REA.description.ilike(term))

    query = query.order_by(REA.created_at.desc())

    return db.paginate(query, page=page, per_page=per_page, error_out=False)


def list_recommended(user_id: uuid.UUID, limit: int) -> list[tuple]:
    score_subq = (
        db.select(
            REATag.rea_id,
            func.coalesce(func.sum(UserTagInterest.weight), 0.0).label("score"),
        )
        .outerjoin(
            UserTagInterest,
            (UserTagInterest.tag_id == REATag.tag_id)
            & (UserTagInterest.user_id == user_id),
        )
        .group_by(REATag.rea_id)
        .subquery()
    )

    query = (
        db.select(REA, func.coalesce(score_subq.c.score, 0.0).label("relevance_score"))
        .outerjoin(score_subq, score_subq.c.rea_id == REA.id)
        .where(REA.status == StatusREAEnum.ativo)
        .order_by(
            func.coalesce(score_subq.c.score, 0.0).desc(),
            REA.avg_rating.desc(),
        )
        .limit(limit)
    )

    return list(db.session.execute(query))


def find_by_id(rea_id) -> REA | None:
    return db.session.get(REA, rea_id)


def find_tags(rea_id: uuid.UUID) -> list[REATag]:
    result = db.session.execute(db.select(REATag).where(REATag.rea_id == rea_id))
    return list(result.scalars())


def find_by_url(url: str) -> REA | None:
    return db.session.execute(db.select(REA).where(REA.url == url)).scalar_one_or_none()


def add_tags(rea_id: uuid.UUID, tag_ids: list[int]) -> None:
    existing = {rt.tag_id for rt in find_tags(rea_id)}
    for tag_id in tag_ids:
        if tag_id not in existing:
            db.session.add(REATag(rea_id=rea_id, tag_id=tag_id))
    db.session.commit()


def create(data: dict) -> REA:
    rea = REA(**data)
    db.session.add(rea)
    db.session.commit()
    return rea
