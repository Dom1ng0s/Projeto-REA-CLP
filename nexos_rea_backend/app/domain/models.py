import uuid
from datetime import datetime
from enum import Enum as PyEnum
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID

db = SQLAlchemy()

class RoleEnum(PyEnum):
    usuario = "usuario"
    admin = "admin"

class StatusModeracaoEnum(PyEnum):
    ativo = "ativo"
    oculto = "oculto"
    sob_revisao = "sob_revisao"

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    nome_completo = db.Column(db.String(150), nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(RoleEnum), default=RoleEnum.usuario, nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

class REA(db.Model):
    __tablename__ = 'reas'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    titulo = db.Column(db.String(255), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    url_origem = db.Column(db.String(500), nullable=False)
    media_notas = db.Column(db.Numeric(3, 2), default=0.00)
    contagem_denuncias = db.Column(db.Integer, default=0)
    status_moderacao = db.Column(db.Enum(StatusModeracaoEnum), default=StatusModeracaoEnum.ativo, nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)