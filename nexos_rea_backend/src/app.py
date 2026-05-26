from flask import Flask
from flask_jwt_extended import JWTManager

from src.config import Config
from src.extensions.database import db
from src.models import models  # noqa: F401 — importado para registrar os modelos no SQLAlchemy
from src.routes.auth_routes import auth_bp


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    JWTManager(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(auth_bp, url_prefix="/api/auth")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
