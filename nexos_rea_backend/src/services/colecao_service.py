import uuid

from src.repositories import colecao_repository, rea_repository
from src.services import interacao_service


def criar_colecao(user_id: str, data: dict) -> dict:
    name = data.get("name", "").strip()
    if not name:
        raise ValueError("O campo 'name' e obrigatorio.")
    if len(name) > 200:
        raise ValueError("O nome deve ter no maximo 200 caracteres.")

    col = colecao_repository.create(
        user_id=uuid.UUID(user_id),
        name=name,
        is_public=bool(data.get("is_public", False)),
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
    if not rea or not rea.is_visible or rea.is_blocked:
        raise LookupError("REA nao encontrado.")

    cid = uuid.UUID(collection_id)
    if colecao_repository.find_item(cid, rid):
        raise ValueError("Este REA ja esta na colecao.")

    item = colecao_repository.add_item(cid, rid)
    interacao_service.recalcular_pesos(user_id, rea_id, "adicionar_colecao")
    return {
        "collection_id": str(item.collection_id),
        "rea_id": str(item.rea_id),
        "added_at": item.added_at.isoformat(),
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
    interacao_service.recalcular_pesos(user_id, rea_id, "remover_colecao")


# --- helpers privados ---

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
        "id": str(col.id),
        "name": col.name,
        "is_public": col.is_public,
        "item_count": len(col.items),
        "created_at": col.created_at.isoformat(),
    }


def _serialize_with_items(col) -> dict:
    return {
        **_serialize(col),
        "items": [
            {
                "rea_id": str(item.rea_id),
                "added_at": item.added_at.isoformat(),
            }
            for item in col.items
        ],
    }
