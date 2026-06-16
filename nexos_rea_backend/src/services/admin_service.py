from datetime import datetime, timezone

from src.extensions.database import db
from src.models.models import (
    REA,
    Rating,
    Report,
    StatusREAEnum,
    User,
    UserTagInterest,
)


# ── Fila de moderação ──────────────────────────────────────────────────────────

def listar_sob_revisao() -> list[dict]:
    reas = db.session.execute(
        db.select(REA)
        .where(REA.status == StatusREAEnum.sob_revisao)
        .order_by(REA.report_count.desc(), REA.created_at.asc())
    ).scalars().all()
    return [_serialize_rea_admin(r) for r in reas]


def aprovar_rea(rea_id: str) -> dict:
    """
    Admin julga o conteúdo como adequado:
    - Restaura status para ATIVO.
    - Marca todas as denúncias pendentes como revisadas.
    """
    rea = _get_or_raise(rea_id)
    if rea.status != StatusREAEnum.sob_revisao:
        raise ValueError("REA nao esta sob revisao.")

    rea.status = StatusREAEnum.ativo
    now = datetime.now(timezone.utc)

    db.session.execute(
        db.update(Report)
        .where(Report.rea_id == rea.id, Report.reviewed == False)  # noqa: E712
        .values(reviewed=True, reviewed_at=now)
    )
    db.session.commit()
    return _serialize_rea_admin(rea)


def remover_rea(rea_id: str) -> dict:
    """
    Admin julga o conteúdo como inadequado e o remove definitivamente.
    O CASCADE no banco cuida de ratings, reports e collection_items.
    """
    rea = _get_or_raise(rea_id)
    payload = {"id": rea_id, "title": rea.title, "removido": True}
    db.session.delete(rea)
    db.session.commit()
    return payload


# ── Dashboard de estatísticas ──────────────────────────────────────────────────

def obter_estatisticas() -> dict:
    total_usuarios = db.session.execute(db.select(db.func.count(User.id))).scalar_one()
    total_ativos = _contar_reas(StatusREAEnum.ativo)
    total_ocultos = _contar_reas(StatusREAEnum.oculto)
    total_sob_revisao = _contar_reas(StatusREAEnum.sob_revisao)
    total_reas = total_ativos + total_ocultos + total_sob_revisao

    total_avaliacoes = db.session.execute(db.select(db.func.count(Rating.id))).scalar_one()
    total_denuncias = db.session.execute(db.select(db.func.count(Report.id))).scalar_one()

    # Taxa de Engajamento: % de usuários que interagiram com ao menos 1 REA.
    # Proxy derivado do perfil de interesses gerado pelo motor de recomendação.
    usuarios_com_interacao = db.session.execute(
        db.select(db.func.count(db.func.distinct(UserTagInterest.user_id)))
    ).scalar_one()

    taxa_engajamento = (
        round(usuarios_com_interacao / total_usuarios * 100, 1)
        if total_usuarios > 0 else 0.0
    )

    return {
        "usuarios": {
            "total": total_usuarios,
            "com_interacao": usuarios_com_interacao,
            "taxa_engajamento_pct": taxa_engajamento,
        },
        "reas": {
            "total": total_reas,
            "ativos": total_ativos,
            "ocultos_automaticamente": total_ocultos,
            "sob_revisao": total_sob_revisao,
        },
        "moderacao": {
            "total_avaliacoes": total_avaliacoes,
            "total_denuncias": total_denuncias,
        },
    }


# ── Helpers ────────────────────────────────────────────────────────────────────

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


def _contar_reas(status: StatusREAEnum) -> int:
    return db.session.execute(
        db.select(db.func.count(REA.id)).where(REA.status == status)
    ).scalar_one()


def _serialize_rea_admin(rea: REA) -> dict:
    denuncias = [
        {
            "id": r.id,
            "user_id": str(r.user_id),
            "reason": r.reason,
            "detail": r.detail,
            "created_at": r.created_at.isoformat(),
            "reviewed": r.reviewed,
        }
        for r in rea.reports
    ]
    return {
        "id": str(rea.id),
        "title": rea.title,
        "url": rea.url,
        "avg_rating": rea.avg_rating,
        "rating_count": rea.rating_count,
        "report_count": rea.report_count,
        "status": rea.status.value,
        "submitted_by": str(rea.submitted_by) if rea.submitted_by else None,
        "created_at": rea.created_at.isoformat(),
        "denuncias": denuncias,
    }
