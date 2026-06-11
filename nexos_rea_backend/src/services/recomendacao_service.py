import uuid

from src.repositories import perfil_repository, rea_repository

_DEFAULT_LIMIT = 20
_MAX_LIMIT = 50


def recomendar(user_id: str, limit: int = _DEFAULT_LIMIT) -> list[dict]:
    limit = min(limit, _MAX_LIMIT)
    uid = uuid.UUID(user_id)

    interests = perfil_repository.list_interests(uid)

    if not interests:
        pagination = rea_repository.list_visible(q=None, page=1, per_page=limit)
        return [_serialize(rea, 0.0) for rea in pagination.items]

    rows = rea_repository.list_recommended(uid, limit)
    return [_serialize(rea, float(score)) for rea, score in rows]


def _serialize(rea, relevance_score: float) -> dict:
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
        "relevance_score": round(relevance_score, 2),
    }
