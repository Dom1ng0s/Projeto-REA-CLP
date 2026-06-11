from flask import Flask
from flask_jwt_extended import JWTManager

from src.config import Config
from src.extensions.database import db
from src.models import models  # noqa: F401 — importado para registrar os modelos no SQLAlchemy
from src.routes.auth_routes import auth_bp
from src.routes.colecoes_routes import colecoes_bp
from src.routes.perfil_routes import perfil_bp
from src.routes.rea_routes import rea_bp
from src.routes.recomendacao_routes import recomendacao_bp


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    JWTManager(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(rea_bp, url_prefix="/api/reas")
    app.register_blueprint(colecoes_bp, url_prefix="/api/colecoes")
    app.register_blueprint(perfil_bp, url_prefix="/api/perfil")
    app.register_blueprint(recomendacao_bp, url_prefix="/api/recomendacoes")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
