import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev_secret_key_local_temporaria_2026xx")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev_jwt_secret_local_temporaria_2026xx")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=2)

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_AS_ASCII = False

    _LOCAL_DB = "postgresql+psycopg://postgres:postgres@localhost:5432/nexos_rea"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", _LOCAL_DB)