import uuid

from sqlalchemy.exc import IntegrityError

from src.extensions.database import db
from src.models.models import REA, Report, StatusREAEnum

# ── Limiares de negócio ────────────────────────────────────────────────────────
_LIMIAR_NOTA_BAIXA: float = 2.0
_LIMIAR_DENUNCIAS: int = 3

MOTIVOS_VALIDOS = frozenset({
    "conteudo_inapropriado",
    "link_quebrado",
    "informacao_incorreta",
    "direitos_autorais",
    "spam",
    "outro",
})


# ── Gatilhos de qualidade ──────────────────────────────────────────────────────

def aplicar_gatilho_avaliacao(rea: REA) -> bool:
    """
    Acionado após avg_rating ser recalculado.

    Regras:
    - avg_rating < 2.0 com ao menos 1 avaliação → status = OCULTO
    - nota melhora acima de 2.0 e status era OCULTO → restaura para ATIVO
    - status SOB_REVISAO tem precedência; este gatilho não o altera.

    Não faz commit — responsabilidade do chamador.
    Retorna True se o status foi alterado.
    """
    if rea.status == StatusREAEnum.sob_revisao:
        return False

    nota_baixa = rea.rating_count > 0 and rea.avg_rating < _LIMIAR_NOTA_BAIXA

    if nota_baixa and rea.status != StatusREAEnum.oculto:
        rea.status = StatusREAEnum.oculto
        return True

    # Restauração automática quando a nota se recupera.
    if not nota_baixa and rea.status == StatusREAEnum.oculto:
        rea.status = StatusREAEnum.ativo
        return True

    return False


def aplicar_gatilho_denuncia(rea: REA) -> bool:
    """
    Acionado após report_count ser incrementado.

    Regra: report_count >= 3 → status = SOB_REVISAO (bloqueia buscas até admin julgar).
    SOB_REVISAO só é revertido por ação explícita de admin.

    Não faz commit — responsabilidade do chamador.
    Retorna True se o status foi alterado.
    """
    if rea.report_count >= _LIMIAR_DENUNCIAS and rea.status != StatusREAEnum.sob_revisao:
        rea.status = StatusREAEnum.sob_revisao
        return True
    return False


# ── Operação de denúncia ───────────────────────────────────────────────────────

def registrar_denuncia(rea_id: str, user_id: str, reason: str, detail: str | None) -> dict:
    """
    Registra a denúncia de um usuário contra um REA, incrementa report_count
    e aplica o gatilho de bloqueio se o limiar for atingido.

    Raises:
        LookupError: REA não encontrado.
        ValueError: motivo inválido ou usuário já denunciou este REA.
    """
    if reason not in MOTIVOS_VALIDOS:
        raise ValueError(f"Motivo invalido. Use: {', '.join(sorted(MOTIVOS_VALIDOS))}.")

    uid = uuid.UUID(user_id)
    rid = uuid.UUID(rea_id)

    rea = db.session.get(REA, rid)
    if not rea:
        raise LookupError("REA nao encontrado.")

    # Denúncias em REAs já sob revisão são registradas para rastreabilidade do admin.
    ja_denunciou = db.session.execute(
        db.select(Report).where(Report.user_id == uid, Report.rea_id == rid)
    ).scalar_one_or_none()

    if ja_denunciou:
        raise ValueError("Voce ja denunciou este REA.")

    db.session.add(Report(
        user_id=uid,
        rea_id=rid,
        reason=reason,
        detail=detail,
    ))
    rea.report_count += 1
    aplicar_gatilho_denuncia(rea)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ValueError("Voce ja denunciou este REA.")

    return {
        "rea_id": rea_id,
        "report_count": rea.report_count,
        "status": rea.status.value,
    }
