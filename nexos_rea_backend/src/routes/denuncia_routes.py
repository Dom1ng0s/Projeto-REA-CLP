from flask import Blueprint, request

from src.services import moderacao_service
from src.utils.auth import get_current_user_id, jwt_required
from src.utils.responses import error, success

denuncia_bp = Blueprint("denuncias", __name__)


@denuncia_bp.post("/")
@jwt_required
def registrar_denuncia():
    body = request.get_json(silent=True) or {}
    user_id = get_current_user_id()

    rea_id = body.get("rea_id", "").strip()
    reason = body.get("reason", "").strip()
    detail = body.get("detail", "").strip() or None

    if not rea_id or not reason:
        return error("Os campos 'rea_id' e 'reason' sao obrigatorios.", 400)

    try:
        resultado = moderacao_service.registrar_denuncia(
            rea_id=rea_id,
            user_id=user_id,
            reason=reason,
            detail=detail,
        )
        return success(data=resultado, status=201)
    except LookupError as e:
        return error(str(e), 404)
    except ValueError as e:
        return error(str(e), 400)
