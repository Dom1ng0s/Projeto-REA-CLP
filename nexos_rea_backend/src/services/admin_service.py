from datetime import datetime, timezone

from src.extensions.database import db
from src.models.models import (
    REA, REARating, REAReport, UserInterest,
    REA_STATUS_ACTIVE, REA_STATUS_HIDDEN, REA_STATUS_REVIEW, REA_STATUS_REMOVED,
)


def listar_sob_revisao() -> list[dict]:
    reas = db.session.execute(
        db.select(REA)
        .where(REA.status.in_([REA_STATUS_REVIEW, REA_STATUS_HIDDEN]))
        .order_by(REA.report_count.desc(), REA.created_at.asc())
    ).scalars().all()
    return [_serialize_rea_admin(r) for r in reas]


def aprovar_rea(rea_id: str) -> dict:
    rea = _get_or_raise(rea_id)
    if rea.status not in (REA_STATUS_REVIEW, REA_STATUS_HIDDEN):
        raise ValueError("REA nao esta sob revisao.")

    rea.status = REA_STATUS_ACTIVE
    now = datetime.now(timezone.utc)

    db.session.execute(
        db.update(REAReport)
        .where(REAReport.rea_id == rea.id, REAReport.state == "pending")
        .values(state="dismissed", resolved_at=now)
    )
    db.session.commit()
    return _serialize_rea_admin(rea)


def remover_rea(rea_id: str) -> dict:
    rea = _get_or_raise(rea_id)
    payload = {"id": rea_id, "title": rea.title, "removido": True}
    db.session.delete(rea)
    db.session.commit()
    return payload


def obter_estatisticas() -> dict:
    total_ativos      = _contar_reas(REA_STATUS_ACTIVE)
    total_ocultos     = _contar_reas(REA_STATUS_HIDDEN)
    total_sob_revisao = _contar_reas(REA_STATUS_REVIEW)
    total_removidos   = _contar_reas(REA_STATUS_REMOVED)
    total_reas        = total_ativos + total_ocultos + total_sob_revisao + total_removidos

    total_avaliacoes = db.session.execute(db.select(db.func.count(REARating.id))).scalar_one()
    total_denuncias  = db.session.execute(db.select(db.func.count(REAReport.id))).scalar_one()

    total_usuarios = db.session.execute(
        db.select(db.func.count(db.func.distinct(UserInterest.user_id)))
    ).scalar_one()

    return {
        "reas": {
            "total":                  total_reas,
            "ativos":                 total_ativos,
            "ocultos_automaticamente": total_ocultos,
            "sob_revisao":            total_sob_revisao,
            "removidos":              total_removidos,
        },
        "moderacao": {
            "total_avaliacoes": total_avaliacoes,
            "total_denuncias":  total_denuncias,
        },
        "usuarios": {
            "com_interacao": total_usuarios,
        },
    }


def _get_or_raise(rea_id: str) -> REA:
    import uuid
    try:
        rid = uuid.UUID(rea_id)
    except (ValueError, AttributeError):
        raise LookupError("REA nao encontrado.")
    rea = db.session.get(REA, rid)
    if not rea:
        raise LookupError("REA nao encontrado.")
    return rea


def _contar_reas(status: str) -> int:
    return db.session.execute(
        db.select(db.func.count(REA.id)).where(REA.status == status)
    ).scalar_one()


def _serialize_rea_admin(rea: REA) -> dict:
    denuncias = [
        {
            "id":         str(r.id),
            "user_id":    str(r.user_id),
            "reason":     r.reason,
            "details":    r.details,
            "created_at": r.created_at.isoformat(),
            "state":      r.state,
        }
        for r in rea.reports
    ]
    return {
        "id":           str(rea.id),
        "title":        rea.title,
        "resource_url": rea.resource_url,
        "rating_avg":   float(rea.rating_avg),
        "rating_count": rea.rating_count,
        "report_count": rea.report_count,
        "status":       rea.status,
        "submitted_by": str(rea.submitted_by) if rea.submitted_by else None,
        "created_at":   rea.created_at.isoformat(),
        "denuncias":    denuncias,
    }
