from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from src.services import recomendacao_service
from src.utils.responses import error, success

recomendacao_bp = Blueprint("recomendacoes", __name__)


@recomendacao_bp.get("/")
@jwt_required()
def recomendar():
    try:
        limit = max(1, int(request.args.get("limit", 20)))
    except ValueError:
        return error("Parâmetro 'limit' inválido.", 400)

    user_id = get_jwt_identity()
    resultado = recomendacao_service.recomendar(user_id=user_id, limit=limit)
    return success(data=resultado)
