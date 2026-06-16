from flask import Blueprint, request

from src.services import perfil_service
from src.utils.auth import get_current_user_id, jwt_required
from src.utils.responses import error, success

perfil_bp = Blueprint("perfil", __name__)


@perfil_bp.get("/interesses")
@jwt_required
def get_interesses():
    user_id = get_current_user_id()
    interests = perfil_service.get_interesses(user_id=user_id)
    return success(data=interests)


@perfil_bp.put("/interesses")
@jwt_required
def atualizar_interesses():
    body = request.get_json(silent=True) or {}
    user_id = get_current_user_id()
    payload = body.get("interesses", [])
    try:
        interests = perfil_service.atualizar_interesses(user_id=user_id, payload=payload)
        return success(data=interests)
    except LookupError as e:
        return error(str(e), 404)
    except ValueError as e:
        return error(str(e), 400)
