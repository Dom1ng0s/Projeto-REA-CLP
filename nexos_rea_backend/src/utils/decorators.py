from functools import wraps

from flask import g
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from src.models.models import RoleEnum
from src.repositories import user_repository
from src.utils.responses import error


def admin_required(fn):
    """Garante que apenas usuários com role=admin acessem a rota."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user = user_repository.find_by_id(get_jwt_identity())
        if not user or not user.is_active or user.role != RoleEnum.admin:
            return error("Acesso restrito a administradores.", 403)
        g.admin = user
        return fn(*args, **kwargs)
    return wrapper
