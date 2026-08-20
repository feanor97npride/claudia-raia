from flask import Flask
from flask_cors import CORS

from .config import Config
from .extensions import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    from .api.meta import bp as meta_bp
    from .api.demandas import bp as demandas_bp
    from .api.projetos import bp as projetos_bp
    from .api.sistemas import bp as sistemas_bp
    from .api.ativos import bp as ativos_bp
    from .api.documentos import bp as documentos_bp
    from .api.dashboard import bp as dashboard_bp

    app.register_blueprint(meta_bp)
    app.register_blueprint(demandas_bp)
    app.register_blueprint(projetos_bp)
    app.register_blueprint(sistemas_bp)
    app.register_blueprint(ativos_bp)
    app.register_blueprint(documentos_bp)
    app.register_blueprint(dashboard_bp)

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    with app.app_context():
        db.create_all()

    return app
