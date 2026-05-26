from src.extensions.database import db
from src.models.models import REA


def list_visible(q: str | None, page: int, per_page: int):
    query = db.select(REA).where(REA.is_visible == True, REA.is_blocked == False)

    if q:
        term = f"%{q}%"
        query = query.where(REA.title.ilike(term) | REA.description.ilike(term))

    query = query.order_by(REA.created_at.desc())

    return db.paginate(query, page=page, per_page=per_page, error_out=False)


def find_by_id(rea_id) -> REA | None:
    return db.session.get(REA, rea_id)


def find_by_url(url: str) -> REA | None:
    return db.session.execute(db.select(REA).where(REA.url == url)).scalar_one_or_none()


def create(data: dict) -> REA:
    rea = REA(**data)
    db.session.add(rea)
    db.session.commit()
    return rea
