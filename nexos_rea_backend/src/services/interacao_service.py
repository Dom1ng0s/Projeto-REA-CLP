import uuid

from src.repositories import perfil_repository, rea_repository

_DELTAS: dict[str, float] = {
    "visualizacao":       0.5,
    "adicionar_colecao":  1.5,
    "remover_colecao":   -0.5,
    "avaliacao_positiva": 2.0,   # score 4-5
    "avaliacao_negativa": -1.0,  # score 1-2
}

EVENTOS_VALIDOS = set(_DELTAS.keys())


def recalcular_pesos(user_id: str, rea_id: str, evento: str) -> None:
    if evento not in _DELTAS:
        raise ValueError(f"Evento invalido. Use: {', '.join(sorted(EVENTOS_VALIDOS))}.")

    delta = _DELTAS[evento]
    uid = uuid.UUID(user_id)
    rid = uuid.UUID(rea_id)

    tags = rea_repository.find_tags(rid)
    for tag in tags:
        perfil_repository.upsert_weight(uid, tag.tag_id, delta)


def evento_para_avaliacao(score: int) -> str:
    if score >= 4:
        return "avaliacao_positiva"
    if score <= 2:
        return "avaliacao_negativa"
    return ""
