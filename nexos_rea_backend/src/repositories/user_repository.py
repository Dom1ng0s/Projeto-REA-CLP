from src.extensions.database import db
from src.models.models import User


def find_by_email(email: str) -> User | None:
    return db.session.execute(
        db.select(User).filter_by(email=email)
    ).scalar_one_or_none()


def find_by_id(user_id) -> User | None:
    return db.session.get(User, user_id)


def create(name: str, email: str, password_hash: str) -> User:
    user = User(name=name, email=email, password_hash=password_hash)
    db.session.add(user)
    db.session.commit()
    return user
