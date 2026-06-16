import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev_secret_key_local_temporaria_2026xx")
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
    SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_AS_ASCII = False

    _SUPABASE_DB = "postgresql+psycopg://postgres:postgres@localhost:5432/nexos_rea"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", _SUPABASE_DB)
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_size": 5, "max_overflow": 10}
