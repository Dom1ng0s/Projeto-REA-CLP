import uuid

from src.repositories import colecao_repository, rea_repository
from src.models.models import REA_STATUS_ACTIVE
from src.services import interacao_service

_VISIBILITY_OPTS = {"private", "public"}


def criar_colecao(user_id: str, data: dict) -> dict:
    title = data.get("title", "").strip()
    if not title:
        raise ValueError("O campo 'title' e obrigatorio.")
    if len(title) > 200:
        raise ValueError("O titulo deve ter no maximo 200 caracteres.")

    visibility = data.get("visibility", "private")
    if visibility not in _VISIBILITY_OPTS:
        raise ValueError(f"Visibilidade invalida. Use: {', '.join(_VISIBILITY_OPTS)}.")

    col = colecao_repository.create(
        user_id=uuid.UUID(user_id),
        title=title,
        visibility=visibility,
    )
    return _serialize(col)


def listar_colecoes(user_id: str) -> list[dict]:
    cols = colecao_repository.list_by_user(uuid.UUID(user_id))
    return [_serialize(c) for c in cols]


def detalhar_colecao(user_id: str, collection_id: str) -> dict:
    col = _get_or_raise(collection_id)
    _assert_owner(col, user_id)
    return _serialize_with_items(col)


def deletar_colecao(user_id: str, collection_id: str) -> None:
    col = _get_or_raise(collection_id)
    _assert_owner(col, user_id)
    colecao_repository.delete(col)


def adicionar_rea(user_id: str, collection_id: str, rea_id: str) -> dict:
    col = _get_or_raise(collection_id)
    _assert_owner(col, user_id)

    try:
        rid = uuid.UUID(rea_id)
    except (ValueError, AttributeError):
        raise ValueError("ID de REA invalido.")

    rea = rea_repository.find_by_id(rid)
    if not rea or rea.status != REA_STATUS_ACTIVE:
        raise LookupError("REA nao encontrado.")

    cid = uuid.UUID(collection_id)
    if colecao_repository.find_item(cid, rid):
        raise ValueError("Este REA ja esta na colecao.")

    item = colecao_repository.add_item(cid, rid)
    interacao_service.registrar_interacao(user_id, rea_id, "adicionar_colecao")
    return {
        "collection_id": str(item.collection_id),
        "rea_id":        str(item.rea_id),
        "added_at":      item.added_at.isoformat(),
    }


def remover_rea(user_id: str, collection_id: str, rea_id: str) -> None:
    col = _get_or_raise(collection_id)
    _assert_owner(col, user_id)

    try:
        cid = uuid.UUID(collection_id)
        rid = uuid.UUID(rea_id)
    except (ValueError, AttributeError):
        raise ValueError("ID invalido.")

    item = colecao_repository.find_item(cid, rid)
    if not item:
        raise LookupError("REA nao encontrado nesta colecao.")

    colecao_repository.remove_item(item)
    interacao_service.registrar_interacao(user_id, rea_id, "remover_colecao")


def _get_or_raise(collection_id: str):
    try:
        cid = uuid.UUID(collection_id)
    except (ValueError, AttributeError):
        raise LookupError("Colecao nao encontrada.")

    col = colecao_repository.find_by_id(cid)
    if not col:
        raise LookupError("Colecao nao encontrada.")
    return col


def _assert_owner(col, user_id: str) -> None:
    if str(col.user_id) != user_id:
        raise PermissionError("Acesso negado.")


def _serialize(col) -> dict:
    return {
        "id":         str(col.id),
        "title":      col.title,
        "visibility": col.visibility,
        "is_system":  col.is_system,
        "item_count": len(col.items),
        "created_at": col.created_at.isoformat(),
    }


def _serialize_with_items(col) -> dict:
    return {
        **_serialize(col),
        "items": [
            {
                "rea_id":   str(item.rea_id),
                "position": item.position,
                "added_at": item.added_at.isoformat(),
            }
            for item in col.items
        ],
    }
