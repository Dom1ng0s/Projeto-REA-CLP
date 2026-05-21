import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy.dialects.postgresql import UUID

# Importamos o db diretamente da nossa camada de infraestrutura
from src.infrastructure.database import db

class RoleEnum(PyEnum):
    usuario = "usuario"
    admin = "admin"

# ... (restante do código das classes Usuario e REA continua igual)