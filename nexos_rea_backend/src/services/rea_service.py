import uuid

from src.extensions.database import db
from src.models.models import REA, REARating, REA_STATUS_ACTIVE
from src.repositories import rea_repository
from src.services import interacao_service, moderacao_service

_ALLOWED_FORMATS = {"video", "audio", "text", "image", "interactive", "slides", "other"}
_MAX_PER_PAGE = 50


def list_reas(
    q: str | None,
    page: int,
    per_page: int,
    format: str | None = None,
    education_level: str | None = None,
    subject_area: str | None = None,
    language: str | None = None,
    min_rating: float | None = None,
    unrated_only: bool = False,
) -> dict:
    per_page = min(per_page, _MAX_PER_PAGE)
    pagination = rea_repository.list_visible(
        q=q, page=page, per_page=per_page,
        format=format, education_level=education_level,
        subject_area=subject_area, language=language,
        min_rating=min_rating, unrated_only=unrated_only,
    )
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
    rea = _get_active_or_raise(rea_id)
    return _serialize(rea)


def submit_rea(data: dict, user_id: str) -> dict:
    _validate(data)

    resource_url = data["resource_url"].strip()
    if rea_repository.find_by_url(resource_url):
        raise ValueError("Ja existe um REA cadastrado com essa URL.")

    rea = rea_repository.create({
        "title":           data["title"].strip(),
        "description":     data.get("description", "").strip() or None,
        "resource_url":    resource_url,
        "author":          data.get("author", "").strip() or None,
        "license":         data["license"].strip(),
        "format":          data["format"].strip().lower(),
        "language":        data.get("language", "pt_br").strip(),
        "subject_area":    data["subject_area"].strip(),
        "education_level": data["education_level"].strip(),
        "thumbnail_url":   data.get("thumbnail_url", "").strip() or None,
        "tags":            data.get("tags", []),
        "submitted_by":    uuid.UUID(user_id),
    })
    return _serialize(rea)


def avaliar_rea(data: dict, rea_id: str, user_id: str) -> dict:
    rating_val = data.get("score") or data.get("rating")
    if not isinstance(rating_val, int) or not (1 <= rating_val <= 5):
        raise ValueError("O campo 'score' deve ser um inteiro entre 1 e 5.")

    rea = _get_active_or_raise(rea_id)
    uid = uuid.UUID(user_id)
    rid = rea.id

    existing = db.session.execute(
        db.select(REARating).where(REARating.user_id == uid, REARating.rea_id == rid)
    ).scalar_one_or_none()

    if existing:
        existing.rating = rating_val
        existing.comment = data.get("comment", existing.comment)
    else:
        db.session.add(REARating(
            user_id=uid,
            rea_id=rid,
            rating=rating_val,
            comment=data.get("comment"),
        ))

    db.session.commit()

    # Supabase trigger (recompute_rea_rating) recalcula rating_avg e status automaticamente.
    # Registra a interação para o motor de recomendação.
    evento = interacao_service.evento_para_avaliacao(rating_val)
    if evento:
        interacao_service.registrar_interacao(user_id, rea_id, evento, value=float(rating_val))

    db.session.refresh(rea)
    return {
        "rea_id": rea_id,
        "rating": rating_val,
        "rating_avg": float(rea.rating_avg),
        "rating_count": rea.rating_count,
    }


def classificar_rea(rea_id: str, data: dict, user_id: str) -> dict:
    rea = _get_active_or_raise(rea_id)

    tags = data.get("tags", [])
    if not isinstance(tags, list) or not tags:
        raise ValueError("O campo 'tags' deve ser uma lista nao-vazia de strings.")

    validated = [str(t).strip().lower() for t in tags if str(t).strip()]
    if not validated:
        raise ValueError("Nenhuma tag valida fornecida.")

    existing = set(rea.tags or [])
    rea.tags = list(existing | set(validated))
    db.session.commit()

    return {"rea_id": rea_id, "tags": rea.tags}


def _get_active_or_raise(rea_id: str) -> REA:
    try:
        rea = rea_repository.find_by_id(uuid.UUID(rea_id))
    except (ValueError, AttributeError):
        raise ValueError("REA nao encontrado.")

    if not rea or rea.status != REA_STATUS_ACTIVE:
        raise ValueError("REA nao encontrado.")
    return rea


def _validate(data: dict) -> None:
    required = ["title", "resource_url", "license", "format", "subject_area", "education_level"]
    for field in required:
        if not data.get(field, "").strip():
            raise ValueError(f"O campo '{field}' e obrigatorio.")

    if data["format"].strip().lower() not in _ALLOWED_FORMATS:
        raise ValueError(f"Formato invalido. Use: {', '.join(sorted(_ALLOWED_FORMATS))}.")


def _serialize(rea) -> dict:
    return {
        "id":              str(rea.id),
        "title":           rea.title,
        "description":     rea.description,
        "resource_url":    rea.resource_url,
        "source_url":      rea.source_url,
        "author":          rea.author,
        "license":         rea.license,
        "format":          rea.format,
        "language":        rea.language,
        "subject_area":    rea.subject_area,
        "education_level": rea.education_level,
        "tags":            rea.tags or [],
        "thumbnail_url":   rea.thumbnail_url,
        "rating_avg":      float(rea.rating_avg),
        "rating_count":    rea.rating_count,
        "report_count":    rea.report_count,
        "status":          rea.status,
        "submitted_by":    str(rea.submitted_by) if rea.submitted_by else None,
        "created_at":      rea.created_at.isoformat(),
        "updated_at":      rea.updated_at.isoformat(),
    }
