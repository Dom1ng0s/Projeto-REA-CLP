from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from src.services import auth_service
from src.utils.responses import error, success

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
def register():
    body = request.get_json(silent=True) or {}
    try:
        user = auth_service.register(
            name=body.get("name", "").strip(),
            email=body.get("email", "").strip().lower(),
            password=body.get("password", ""),
        )
        return success(data=user, status=201)
    except ValueError as e:
        return error(str(e), 400)


@auth_bp.post("/login")
def login():
    body = request.get_json(silent=True) or {}
    try:
        result = auth_service.login(
            email=body.get("email", "").strip().lower(),
            password=body.get("password", ""),
        )
        return success(data=result)
    except ValueError as e:
        return error(str(e), 401)


@auth_bp.get("/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()
    try:
        user = auth_service.get_me(user_id)
        return success(data=user)
    except ValueError as e:
        return error(str(e), 404)
