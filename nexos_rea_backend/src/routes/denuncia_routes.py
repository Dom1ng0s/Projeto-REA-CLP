from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from src.services import moderacao_service
from src.utils.responses import error, success

denuncia_bp = Blueprint("denuncias", __name__)


@denuncia_bp.post("/")
@jwt_required()
def registrar_denuncia():
    """
    POST /api/denuncias
    Body: { "rea_id": str, "reason": str, "detail": str (opcional) }

    Qualquer usuário autenticado pode denunciar um REA uma única vez.
    O serviço de moderação aplica automaticamente o gatilho de bloqueio
    ao atingir 3 denúncias.
    """
    body = request.get_json(silent=True) or {}
    user_id = get_jwt_identity()

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
