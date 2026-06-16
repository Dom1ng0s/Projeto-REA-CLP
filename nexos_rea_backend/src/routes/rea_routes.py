from flask import Blueprint, request

from src.services import interacao_service, rea_service
from src.utils.auth import get_current_user_id, jwt_required
from src.utils.responses import error, success

rea_bp = Blueprint("reas", __name__)


@rea_bp.get("/")
def list_reas():
    q = request.args.get("q", "").strip() or None
    try:
        page = max(1, int(request.args.get("page", 1)))
        per_page = max(1, int(request.args.get("per_page", 10)))
    except ValueError:
        return error("Parametros de paginacao invalidos.", 400)

    result = rea_service.list_reas(q=q, page=page, per_page=per_page)
    return success(data=result)


@rea_bp.get("/<string:rea_id>")
def get_rea(rea_id: str):
    try:
        rea = rea_service.get_rea(rea_id)
        return success(data=rea)
    except ValueError as e:
        return error(str(e), 404)


@rea_bp.post("/")
@jwt_required
def submit_rea():
    body = request.get_json(silent=True) or {}
    user_id = get_current_user_id()
    try:
        rea = rea_service.submit_rea(data=body, user_id=user_id)
        return success(data=rea, status=201)
    except ValueError as e:
        return error(str(e), 400)


@rea_bp.post("/<string:rea_id>/visualizacao")
@jwt_required
def registrar_visualizacao(rea_id: str):
    user_id = get_current_user_id()
    try:
        rea_service.get_rea(rea_id)
        interacao_service.registrar_interacao(user_id, rea_id, "view")
        return success(message="Visualizacao registrada.")
    except ValueError as e:
        return error(str(e), 404)


@rea_bp.post("/<string:rea_id>/avaliacoes")
@jwt_required
def avaliar_rea(rea_id: str):
    body = request.get_json(silent=True) or {}
    user_id = get_current_user_id()
    try:
        rea = rea_service.avaliar_rea(data=body, rea_id=rea_id, user_id=user_id)
        return success(data=rea, status=201)
    except LookupError as e:
        return error(str(e), 404)
    except ValueError as e:
        return error(str(e), 400)


@rea_bp.post("/<string:rea_id>/tags")
@jwt_required
def classificar_rea(rea_id: str):
    body = request.get_json(silent=True) or {}
    user_id = get_current_user_id()
    try:
        result = rea_service.classificar_rea(rea_id=rea_id, data=body, user_id=user_id)
        return success(data=result)
    except LookupError as e:
        return error(str(e), 404)
    except ValueError as e:
        return error(str(e), 400)
