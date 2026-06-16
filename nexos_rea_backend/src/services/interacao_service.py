import uuid

from src.extensions.database import db
from src.models.models import REAInteraction

# Mapeamento evento Flask → event_type Supabase
_EVENTO_MAP: dict[str, str] = {
    "visualizacao":       "view",
    "adicionar_colecao":  "save_to_collection",
    "remover_colecao":    "remove_from_collection",
    "avaliacao_positiva": "rating",
    "avaliacao_negativa": "rating",
    "view":               "view",
    "rating":             "rating",
}

EVENTOS_VALIDOS = set(_EVENTO_MAP.keys())


def registrar_interacao(user_id: str, rea_id: str, evento: str, value: float = 0.0) -> None:
    """
    Insere um registro em rea_interactions.
    O trigger recompute_user_interests do Supabase recalcula user_interests automaticamente.
    """
    event_type = _EVENTO_MAP.get(evento, evento)
    db.session.add(REAInteraction(
        user_id=uuid.UUID(user_id),
        rea_id=uuid.UUID(rea_id),
        event_type=event_type,
        value=value,
    ))
    db.session.commit()


def evento_para_avaliacao(score: int) -> str:
    if score >= 4:
        return "avaliacao_positiva"
    if score <= 2:
        return "avaliacao_negativa"
    return ""
