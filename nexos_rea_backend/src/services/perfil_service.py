import uuid

from src.repositories import perfil_repository

_MAX_WEIGHT = 10.0
_MAX_INTERESSES = 50


def get_interesses(user_id: str) -> list[dict]:
    interests = perfil_repository.list_interests(uuid.UUID(user_id))
    return [_serialize(i) for i in interests]


def atualizar_interesses(user_id: str, payload: list) -> list[dict]:
    if not isinstance(payload, list):
        raise ValueError("O campo 'interesses' deve ser uma lista.")
    if len(payload) > _MAX_INTERESSES:
        raise ValueError(f"Limite de {_MAX_INTERESSES} interesses por perfil.")

    validated: list[dict] = []
    seen_tags: set = set()

    for idx, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"Item {idx}: formato invalido.")

        tag_id = item.get("tag_id")
        if not isinstance(tag_id, str):
            raise ValueError(f"Item {idx}: 'tag_id' deve ser um UUID string.")
        if tag_id in seen_tags:
            raise ValueError(f"Item {idx}: tag_id={tag_id} duplicado na lista.")
        seen_tags.add(tag_id)

        try:
            tag_uuid = uuid.UUID(tag_id)
        except ValueError:
            raise ValueError(f"Item {idx}: 'tag_id' invalido.")

        raw_weight = item.get("weight", 1.0)
        try:
            weight = float(raw_weight)
        except (TypeError, ValueError):
            raise ValueError(f"Item {idx}: 'weight' deve ser um numero.")
        if not (0.0 < weight <= _MAX_WEIGHT):
            raise ValueError(f"Item {idx}: 'weight' deve ser > 0 e <= {_MAX_WEIGHT}.")

        if not perfil_repository.find_tag_by_id(tag_uuid):
            raise LookupError(f"Tag com id={tag_id} nao encontrada.")

        validated.append({"tag_id": tag_uuid, "weight": weight})

    interests = perfil_repository.replace_interests(uuid.UUID(user_id), validated)
    return [_serialize(i) for i in interests]


def _serialize(interest) -> dict:
    return {
        "tag_id":   str(interest.tag_id),
        "tag_label": interest.tag.label,
        "tag_slug":  interest.tag.slug,
        "weight":    float(interest.weight),
        "updated_at": interest.updated_at.isoformat(),
    }
