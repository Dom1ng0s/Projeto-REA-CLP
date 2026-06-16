from flask import Flask
from flask_cors import CORS

from src.config import Config
from src.extensions.database import db
from src.models import models  # noqa: F401 — registra os modelos no SQLAlchemy
from src.routes.admin_routes import admin_bp
from src.routes.colecoes_routes import colecoes_bp
from src.routes.denuncia_routes import denuncia_bp
from src.routes.perfil_routes import perfil_bp
from src.routes.rea_routes import rea_bp
from src.routes.recomendacao_routes import recomendacao_bp


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app)
    db.init_app(app)

    app.register_blueprint(rea_bp,          url_prefix="/api/reas")
    app.register_blueprint(colecoes_bp,     url_prefix="/api/colecoes")
    app.register_blueprint(perfil_bp,       url_prefix="/api/perfil")
    app.register_blueprint(recomendacao_bp, url_prefix="/api/recomendacoes")
    app.register_blueprint(denuncia_bp,     url_prefix="/api/denuncias")
    app.register_blueprint(admin_bp,        url_prefix="/api/admin")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
