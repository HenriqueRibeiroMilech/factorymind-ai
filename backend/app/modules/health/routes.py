from pathlib import Path

from flask import Blueprint, current_app, jsonify

bp = Blueprint("health", __name__)


@bp.get("/health")
def health():
    return jsonify(
        status="ok",
        integrations={
            "jev_configured": bool(current_app.config["JEV_API_KEY"]),
            "llm_configured": bool(current_app.config["OPENAI_API_KEY"]),
            "model_available": all((Path(current_app.config["MODEL_DIR"]) / name).is_file()
                                   for name in ("pipeline.joblib", "metadata.json")),
        },
    )
