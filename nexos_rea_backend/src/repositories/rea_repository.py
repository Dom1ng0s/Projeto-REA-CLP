import uuid

from sqlalchemy import func

from src.extensions.database import db
from src.models.models import REA, REA_STATUS_ACTIVE, UserInterest, Tag


def list_visible(q: str | None, page: int, per_page: int):
    query = db.select(REA).where(REA.status == REA_STATUS_ACTIVE)

    if q:
        term = f"%{q}%"
        query = query.where(REA.title.ilike(term) | REA.description.ilike(term))

    query = query.order_by(REA.created_at.desc())
    return db.paginate(query, page=page, per_page=per_page, error_out=False)


def find_by_id(rea_id) -> REA | None:
    return db.session.get(REA, rea_id)


def find_by_url(url: str) -> REA | None:
    return db.session.execute(
        db.select(REA).where(REA.resource_url == url)
    ).scalar_one_or_none()


def create(data: dict) -> REA:
    rea = REA(**data)
    db.session.add(rea)
    db.session.commit()
    return rea


def list_recommended(user_id: uuid.UUID, limit: int) -> list[tuple]:
    # Sprint A: filter REAs whose tags overlap with user's interested tag labels,
    # ordered by rating. Sprint B replaces this with a Supabase RPC call.
    tag_labels_subq = (
        db.select(func.array_agg(Tag.label))
        .join(UserInterest, UserInterest.tag_id == Tag.id)
        .where(UserInterest.user_id == user_id)
        .scalar_subquery()
    )

    reas = db.session.execute(
        db.select(REA)
        .where(
            REA.status == REA_STATUS_ACTIVE,
            REA.tags.overlap(tag_labels_subq),
        )
        .order_by(REA.rating_avg.desc(), REA.created_at.desc())
        .limit(limit)
    ).scalars().all()

    return [(rea, 0.0) for rea in reas]
