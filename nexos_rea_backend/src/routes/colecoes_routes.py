from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from src.services import colecao_service
from src.utils.responses import error, success

colecoes_bp = Blueprint("colecoes", __name__)


@colecoes_bp.post("/")
@jwt_required()
def criar_colecao():
    body = request.get_json(silent=True) or {}
    user_id = get_jwt_identity()
    try:
        col = colecao_service.criar_colecao(user_id=user_id, data=body)
        return success(data=col, status=201)
    except ValueError as e:
        return error(str(e), 400)


@colecoes_bp.get("/")
@jwt_required()
def listar_colecoes():
    user_id = get_jwt_identity()
    cols = colecao_service.listar_colecoes(user_id=user_id)
    return success(data=cols)


@colecoes_bp.get("/<string:collection_id>")
@jwt_required()
def detalhar_colecao(collection_id: str):
    user_id = get_jwt_identity()
    try:
        col = colecao_service.detalhar_colecao(user_id=user_id, collection_id=collection_id)
        return success(data=col)
    except LookupError as e:
        return error(str(e), 404)
    except PermissionError as e:
        return error(str(e), 403)


@colecoes_bp.delete("/<string:collection_id>")
@jwt_required()
def deletar_colecao(collection_id: str):
    user_id = get_jwt_identity()
    try:
        colecao_service.deletar_colecao(user_id=user_id, collection_id=collection_id)
        return success(message="Coleção removida com sucesso.")
    except LookupError as e:
        return error(str(e), 404)
    except PermissionError as e:
        return error(str(e), 403)


@colecoes_bp.post("/<string:collection_id>/items")
@jwt_required()
def adicionar_rea(collection_id: str):
    body = request.get_json(silent=True) or {}
    user_id = get_jwt_identity()
    rea_id = str(body.get("rea_id", "")).strip()
    try:
        item = colecao_service.adicionar_rea(
            user_id=user_id,
            collection_id=collection_id,
            rea_id=rea_id,
        )
        return success(data=item, status=201)
    except LookupError as e:
        return error(str(e), 404)
    except PermissionError as e:
        return error(str(e), 403)
    except ValueError as e:
        return error(str(e), 400)


@colecoes_bp.delete("/<string:collection_id>/items/<string:rea_id>")
@jwt_required()
def remover_rea(collection_id: str, rea_id: str):
    user_id = get_jwt_identity()
    try:
        colecao_service.remover_rea(
            user_id=user_id,
            collection_id=collection_id,
            rea_id=rea_id,
        )
        return success(message="REA removido da coleção.")
    except LookupError as e:
        return error(str(e), 404)
    except PermissionError as e:
        return error(str(e), 403)
    except ValueError as e:
        return error(str(e), 400)
