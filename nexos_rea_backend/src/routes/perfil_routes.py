from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from src.services import perfil_service
from src.utils.responses import error, success

perfil_bp = Blueprint("perfil", __name__)


@perfil_bp.get("/interesses")
@jwt_required()
def get_interesses():
    user_id = get_jwt_identity()
    interests = perfil_service.get_interesses(user_id=user_id)
    return success(data=interests)


@perfil_bp.put("/interesses")
@jwt_required()
def atualizar_interesses():
    body = request.get_json(silent=True) or {}
    user_id = get_jwt_identity()
    payload = body.get("interesses", [])
    try:
        interests = perfil_service.atualizar_interesses(user_id=user_id, payload=payload)
        return success(data=interests)
    except LookupError as e:
        return error(str(e), 404)
    except ValueError as e:
        return error(str(e), 400)
