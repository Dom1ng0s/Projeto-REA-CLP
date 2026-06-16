import re

from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash, generate_password_hash

from src.repositories import user_repository

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def register(name: str, email: str, password: str) -> dict:
    if not name or not email or not password:
        raise ValueError("Todos os campos sao obrigatorios.")
    if not _EMAIL_RE.match(email):
        raise ValueError("E-mail invalido.")
    if len(password) < 6:
        raise ValueError("A senha deve ter pelo menos 6 caracteres.")
    if user_repository.find_by_email(email):
        raise ValueError("E-mail ja cadastrado.")

    password_hash = generate_password_hash(password)
    user = user_repository.create(name=name, email=email, password_hash=password_hash)
    return _serialize(user)


def login(email: str, password: str) -> dict:
    if not email or not password:
        raise ValueError("E-mail e senha sao obrigatorios.")

    user = user_repository.find_by_email(email)
    if not user or not check_password_hash(user.password_hash, password):
        raise ValueError("Credenciais invalidas.")
    if not user.is_active:
        raise ValueError("Conta desativada.")

    token = create_access_token(identity=str(user.id))
    return {"access_token": token, "user": _serialize(user)}


def get_me(user_id: str) -> dict:
    user = user_repository.find_by_id(user_id)
    if not user or not user.is_active:
        raise ValueError("Usuario nao encontrado.")
    return _serialize(user)


def _serialize(user) -> dict:
    return {
        "id": str(user.id),
        "name": user.name,
        "email": user.email,
        "role": user.role.value,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat(),
    }
