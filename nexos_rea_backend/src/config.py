import os
from datetime import timedelta

class Config:
    # Chaves de segurança com fallbacks para desenvolvimento local
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_secret_key_local_temporaria')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'dev_jwt_secret_local_temporaria')
    
    # Tempo de expiração do token JWT para a camada de segurança
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=2)
    
    # Configuração do SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Fallback para o banco de dados local usando o driver psycopg3
    # Altere 'postgres:suasenha' para as credenciais do seu PostgreSQL local
    LOCAL_DATABASE_URL = 'postgresql+psycopg://postgres:postgres@localhost:5432/nexos_rea'
    
    # Se houver variável de ambiente (no deploy), usa ela; do contrário, usa o banco local
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', LOCAL_DATABASE_URL)