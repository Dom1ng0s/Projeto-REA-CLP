import uuid

from src.extensions.database import db
from src.models.models import Rating, StatusREAEnum
from src.repositories import perfil_repository, rea_repository
from src.services import interacao_service, moderacao_service

_ALLOWED_TYPES = {"video", "article", "course", "ebook", "exercise", "other"}
_MAX_PER_PAGE = 50


def list_reas(q: str | None, page: int, per_page: int) -> dict:
    per_page = min(per_page, _MAX_PER_PAGE)
    pagination = rea_repository.list_visible(q=q, page=page, per_page=per_page)

    return {
        "items": [_serialize(r) for r in pagination.items],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        },
    }


def get_rea(rea_id: str) -> dict:
    rea = _get_visible_or_raise(rea_id)
    return _serialize(rea)


def submit_rea(data: dict, user_id: str) -> dict:
    _validate(data)

    url = data["url"].strip()
    if rea_repository.find_by_url(url):
        raise ValueError("Ja existe um REA cadastrado com essa URL.")

    rea = rea_repository.create({
        "title": data["title"].strip(),
        "description": data["description"].strip(),
        "url": data["url"].strip(),
        "author": data.get("author", "").strip() or None,
        "license": data["license"].strip(),
        "resource_type": data["resource_type"].strip().lower(),
        "language": data.get("language", "pt-BR").strip(),
        "thumbnail_url": data.get("thumbnail_url", "").strip() or None,
        "submitted_by": uuid.UUID(user_id),
    })
    return _serialize(rea)


def avaliar_rea(data: dict, rea_id: str, user_id: str) -> dict:
    score = data.get("score")
    if not isinstance(score, int) or not (1 <= score <= 5):
        raise ValueError("O campo 'score' deve ser um inteiro entre 1 e 5.")

    rea = _get_visible_or_raise(rea_id)
    uid = uuid.UUID(user_id)
    rid = rea.id

    existing = db.session.execute(
        db.select(Rating).where(Rating.user_id == uid, Rating.rea_id == rid)
    ).scalar_one_or_none()

    if existing:
        existing.score = score
        existing.comment = data.get("comment", existing.comment)
    else:
        db.session.add(Rating(
            user_id=uid,
            rea_id=rid,
            score=score,
            comment=data.get("comment"),
        ))

    _recalcular_avg_rating(rea)
    moderacao_service.aplicar_gatilho_avaliacao(rea)
    db.session.commit()

    evento = interacao_service.evento_para_avaliacao(score)
    if evento:
        interacao_service.recalcular_pesos(user_id, rea_id, evento)

    return {
        "rea_id": rea_id,
        "score": score,
        "avg_rating": rea.avg_rating,
        "rating_count": rea.rating_count,
    }


def classificar_rea(rea_id: str, data: dict, user_id: str) -> dict:
    rea = _get_visible_or_raise(rea_id)

    tag_ids = data.get("tag_ids", [])
    if not isinstance(tag_ids, list) or not tag_ids:
        raise ValueError("O campo 'tag_ids' deve ser uma lista nao-vazia de inteiros.")

    validated: list[int] = []
    for tid in tag_ids:
        if not isinstance(tid, int) or tid <= 0:
            raise ValueError(f"tag_id invalido: {tid}.")
        if not perfil_repository.find_tag_by_id(tid):
            raise LookupError(f"Tag com id={tid} nao encontrada.")
        validated.append(tid)

    rea_repository.add_tags(rea.id, validated)

    tags = rea_repository.find_tags(rea.id)
    return {
        "rea_id": rea_id,
        "tags": [{"tag_id": t.tag_id} for t in tags],
    }


def _recalcular_avg_rating(rea) -> None:
    result = db.session.execute(
        db.select(
            db.func.avg(Rating.score).label("avg"),
            db.func.count(Rating.id).label("count"),
        ).where(Rating.rea_id == rea.id)
    ).one()
    rea.avg_rating = round(float(result.avg or 0.0), 2)
    rea.rating_count = result.count


def _get_visible_or_raise(rea_id: str):
    try:
        rea = rea_repository.find_by_id(uuid.UUID(rea_id))
    except (ValueError, AttributeError):
        raise ValueError("REA nao encontrado.")

    if not rea or rea.status != StatusREAEnum.ativo:
        raise ValueError("REA nao encontrado.")
    return rea


def _validate(data: dict) -> None:
    required = ["title", "description", "url", "license", "resource_type"]
    for field in required:
        if not data.get(field, "").strip():
            raise ValueError(f"O campo '{field}' e obrigatorio.")

    if data["resource_type"].strip().lower() not in _ALLOWED_TYPES:
        raise ValueError(f"Tipo invalido. Use: {', '.join(sorted(_ALLOWED_TYPES))}.")


def _serialize(rea) -> dict:
    return {
        "id": str(rea.id),
        "title": rea.title,
        "description": rea.description,
        "url": rea.url,
        "author": rea.author,
        "license": rea.license,
        "resource_type": rea.resource_type,
        "language": rea.language,
        "thumbnail_url": rea.thumbnail_url,
        "avg_rating": rea.avg_rating,
        "rating_count": rea.rating_count,
        "submitted_by": str(rea.submitted_by) if rea.submitted_by else None,
        "created_at": rea.created_at.isoformat(),
    }
