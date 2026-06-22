import logging
from functools import wraps

import jwt
from jwt import PyJWKClient
from flask import current_app, g, request

from src.utils.responses import error

logger = logging.getLogger(__name__)

# Cache de clientes JWKS por URL (reutilizado entre requests).
_jwks_clients: dict[str, PyJWKClient] = {}


def _get_jwks_client() -> PyJWKClient:
    url = current_app.config["SUPABASE_URL"]
    if url not in _jwks_clients:
        _jwks_clients[url] = PyJWKClient(
            f"{url}/auth/v1/.well-known/jwks.json",
            cache_keys=True,
        )
    return _jwks_clients[url]


def _get_bearer_token() -> str | None:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return None


def _decode_token(token: str) -> dict:
    header = jwt.get_unverified_header(token)
    if header.get("alg") == "RS256":
        client = _get_jwks_client()
        signing_key = client.get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience="authenticated",
        )
    # HS256: usado nos testes com secret estático.
    return jwt.decode(
        token,
        current_app.config["SUPABASE_JWT_SECRET"],
        algorithms=["HS256"],
        audience="authenticated",
    )


def get_current_user_id() -> str:
    """Retorna o UUID do usuário autenticado (sub claim do JWT do Supabase)."""
    return g.user_id


def jwt_required(fn):
    """Valida o JWT do Supabase e armazena o user_id em g.user_id."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = _get_bearer_token()
        if not token:
            return error("Token de autenticacao ausente.", 401)
        try:
            payload = _decode_token(token)
        except jwt.ExpiredSignatureError:
            return error("Token expirado.", 401)
        except jwt.InvalidTokenError as exc:
            logger.error("JWT inválido [%s]: %s", type(exc).__name__, exc)
            return error("Token invalido.", 422)
        g.user_id = payload["sub"]
        return fn(*args, **kwargs)
    return wrapper
