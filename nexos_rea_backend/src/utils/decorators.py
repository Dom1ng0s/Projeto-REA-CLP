from functools import wraps

from src.extensions.database import db
from src.models.models import UserRole
from src.utils.auth import _decode_token, _get_bearer_token
from src.utils.responses import error


def admin_required(fn):
    """Valida JWT do Supabase e verifica role='admin' em user_roles."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        from flask import g
        token = _get_bearer_token()
        if not token:
            return error("Token de autenticacao ausente.", 401)
        try:
            import jwt as pyjwt
            payload = _decode_token(token)
        except pyjwt.ExpiredSignatureError:
            return error("Token expirado.", 401)
        except pyjwt.InvalidTokenError:
            return error("Token invalido.", 422)

        user_id = payload["sub"]
        import uuid
        is_admin = db.session.execute(
            db.select(UserRole).where(
                UserRole.user_id == uuid.UUID(user_id),
                UserRole.role == "admin",
            )
        ).scalar_one_or_none()

        if not is_admin:
            return error("Acesso restrito a administradores.", 403)

        g.user_id = user_id
        return fn(*args, **kwargs)
    return wrapper
