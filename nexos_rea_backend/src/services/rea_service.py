import uuid

from src.repositories import rea_repository

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


def _get_visible_or_raise(rea_id: str):
    try:
        rea = rea_repository.find_by_id(uuid.UUID(rea_id))
    except (ValueError, AttributeError):
        raise ValueError("REA não encontrado.")

    if not rea or rea.is_blocked or not rea.is_visible:
        raise ValueError("REA não encontrado.")
    return rea


def _validate(data: dict) -> None:
    required = ["title", "description", "url", "license", "resource_type"]
    for field in required:
        if not data.get(field, "").strip():
            raise ValueError(f"O campo '{field}' é obrigatório.")

    if data["resource_type"].strip().lower() not in _ALLOWED_TYPES:
        raise ValueError(f"Tipo inválido. Use: {', '.join(sorted(_ALLOWED_TYPES))}.")


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
