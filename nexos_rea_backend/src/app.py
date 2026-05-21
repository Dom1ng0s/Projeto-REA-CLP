from flask import Flask
from src.config import Config
from src.infrastructure.database import db

# Importamos os modelos para que o SQLAlchemy crie as tabelas corretamente
from src.domain.models import models

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Liga a infraestrutura de base de dados à aplicação
    db.init_app(app)

    with app.app_context():
        # Cria as tabelas na base de dados se não existirem
        db.create_all()

    # (AQUI: na Sprint 2 vamos registar as rotas de autenticação)

    return app

# Bloco de execução para quando rodarmos localmente
if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)