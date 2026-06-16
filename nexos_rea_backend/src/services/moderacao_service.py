import uuid

from sqlalchemy.exc import IntegrityError

from src.extensions.database import db
from src.models.models import REA, REAReport, REA_STATUS_ACTIVE

MOTIVOS_VALIDOS = frozenset({
    "inappropriate",
    "broken_link",
    "copyright",
    "misinformation",
    "spam",
    "other",
})


def registrar_denuncia(rea_id: str, user_id: str, reason: str, detail: str | None) -> dict:
    """
    Registra a denúncia em rea_reports.
    O trigger recompute_rea_reports do Supabase aplica o gatilho de bloqueio automaticamente.
    """
    if reason not in MOTIVOS_VALIDOS:
        raise ValueError(f"Motivo invalido. Use: {', '.join(sorted(MOTIVOS_VALIDOS))}.")

    uid = uuid.UUID(user_id)
    rid = uuid.UUID(rea_id)

    rea = db.session.get(REA, rid)
    if not rea:
        raise LookupError("REA nao encontrado.")

    ja_denunciou = db.session.execute(
        db.select(REAReport).where(REAReport.user_id == uid, REAReport.rea_id == rid)
    ).scalar_one_or_none()

    if ja_denunciou:
        raise ValueError("Voce ja denunciou este REA.")

    db.session.add(REAReport(
        user_id=uid,
        rea_id=rid,
        reason=reason,
        details=detail,
    ))

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ValueError("Voce ja denunciou este REA.")

    db.session.refresh(rea)
    return {
        "rea_id": rea_id,
        "report_count": rea.report_count,
        "status": rea.status,
    }
