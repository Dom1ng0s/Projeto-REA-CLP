import uuid

from sqlalchemy import func

from src.extensions.database import db
from src.models.models import REA, REA_STATUS_ACTIVE, UserInterest, Tag


def list_visible(
    q: str | None,
    page: int,
    per_page: int,
    format: str | None = None,
    education_level: str | None = None,
    subject_area: str | None = None,
    language: str | None = None,
    min_rating: float | None = None,
):
    query = db.select(REA).where(REA.status == REA_STATUS_ACTIVE)

    if q:
        term = f"%{q}%"
        query = query.where(REA.title.ilike(term) | REA.description.ilike(term))
    if format:
        query = query.where(REA.format == format)
    if education_level:
        query = query.where(REA.education_level == education_level)
    if subject_area:
        query = query.where(REA.subject_area == subject_area)
    if language:
        query = query.where(REA.language == language)
    if min_rating is not None:
        query = query.where(REA.rating_avg >= min_rating)

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
    # Flask path for /api/recomendacoes/ — kept for backend API consumers.
    # Frontend uses the Supabase RPC get_recommended_feed() directly (Sprint B).
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
