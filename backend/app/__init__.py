import sqlite3
from pathlib import Path

from flask import Flask, jsonify, send_from_directory
from pydantic import ValidationError
from werkzeug.exceptions import HTTPException

from app.config import ROOT, load_config
from app.errors import AppError


def create_app(test_config=None):
    app = Flask(__name__, static_folder=None)
    app.config.update(load_config())
    if test_config:
        app.config.update(test_config)

    from app.modules.health.routes import bp as health
    from app.modules.incidents.routes import bp as incidents
    from app.modules.incidents.storage import init_db

    app.register_blueprint(health, url_prefix="/api/v1")
    app.register_blueprint(incidents, url_prefix="/api/v1/incidents")
    with app.app_context():
        init_db()

    @app.errorhandler(AppError)
    def handle_app_error(exc):
        return jsonify(error={"code": exc.code, "message": exc.message}), exc.status

    @app.errorhandler(ValidationError)
    def handle_validation(exc):
        return jsonify(error={
            "code": "validation_error",
            "message": "Confira os campos informados.",
            "fields": [{"field": ".".join(map(str, err["loc"])), "message": err["msg"]}
                       for err in exc.errors(include_input=False, include_context=False)],
        }), 422

    @app.errorhandler(HTTPException)
    def handle_http(exc):
        return jsonify(error={"code": "http_error", "message": exc.description}), exc.code

    @app.errorhandler(sqlite3.Error)
    def handle_database(exc):
        app.logger.exception("SQLite operation failed")
        return jsonify(error={"code": "database_error", "message": "Não foi possível acessar o banco. Tente novamente."}), 503

    @app.errorhandler(Exception)
    def handle_unexpected(exc):
        app.logger.exception("Unexpected request failure")
        return jsonify(error={"code": "internal_error", "message": "Não foi possível concluir. Reabra a ocorrência e tente novamente."}), 500

    @app.get("/", defaults={"path": ""})
    @app.get("/<path:path>")
    def frontend(path):
        if path.startswith("api/"):
            return jsonify(error={"code": "not_found", "message": "Rota não encontrada."}), 404
        dist = ROOT / "frontend/dist"
        if not (dist / "index.html").is_file():
            return jsonify(message="API FactoryMind AI. Inicie o Vue com npm run dev ou gere o build."), 200
        candidate = (dist / path).resolve()
        if candidate.is_relative_to(dist.resolve()) and candidate.is_file():
            return send_from_directory(dist, path)
        return send_from_directory(dist, "index.html")

    return app
