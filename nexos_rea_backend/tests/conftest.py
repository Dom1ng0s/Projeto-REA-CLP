import pytest

from src.app import create_app
from src.config import Config
from src.extensions.database import db as _db


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/nexos_rea_test"
    )
    JWT_SECRET_KEY = "test-jwt-secret-key-nexos-rea-2026xx"
    SECRET_KEY = "test-secret-key-nexos-rea-2026xxxxx"


@pytest.fixture(scope="session")
def app():
    application = create_app(TestConfig)
    with application.app_context():
        _db.create_all()
        yield application
        _db.drop_all()


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
