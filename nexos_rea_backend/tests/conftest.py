import os
import time
import uuid as _uuid

import jwt
import pytest
from sqlalchemy.pool import NullPool

from src.app import create_app
from src.config import Config
from src.extensions.database import db as _db

_DEFAULT_TEST_DB = "postgresql+psycopg://postgres:postgres@localhost:5432/nexos_rea_test"

# Shared constant so test modules can import it for ad-hoc token generation.
_TEST_JWT_SECRET = "test-supabase-jwt-secret-nexos-rea-sprint-e!!"


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URL", _DEFAULT_TEST_DB)
    SQLALCHEMY_ENGINE_OPTIONS = {"poolclass": NullPool}
    SUPABASE_JWT_SECRET = _TEST_JWT_SECRET
    SECRET_KEY = os.environ.get("SECRET_KEY", "test-secret-key-nexos-rea-2026xxxxx!!")


@pytest.fixture(scope="session")
def app():
    application = create_app(TestConfig)
    with application.app_context():
        # CASCADE handles stale tables from previous schema iterations.
        _db.session.execute(_db.text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
        _db.session.commit()
        _db.create_all()
        yield application
        _db.session.execute(_db.text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
        _db.session.commit()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def clean_db(app):
    yield
    with app.app_context():
        for table in reversed(_db.metadata.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit()


@pytest.fixture
def make_token():
    """Returns a callable that mints a valid Supabase-style JWT for tests.

    Usage: token = make_token()          → random user_id
           token = make_token(user_id)   → fixed user_id string
    """
    def _mint(user_id: str | None = None) -> str:
        uid = user_id or str(_uuid.uuid4())
        now = int(time.time())
        payload = {
            "sub":  uid,
            "aud":  "authenticated",
            "role": "authenticated",
            "iat":  now,
            "exp":  now + 3600,
        }
        return jwt.encode(payload, _TEST_JWT_SECRET, algorithm="HS256")
    return _mint
