from flask import Blueprint, jsonify, request

from app.errors import AppError
from app.modules.incidents import service, storage
from app.modules.incidents.schemas import CATEGORIES, CreateIncident, Review, UpdateContext

bp = Blueprint("incidents", __name__)


@bp.get("/categories")
def categories():
    return jsonify(CATEGORIES)


@bp.post("")
def create():
    data = CreateIncident.model_validate(request.get_json())
    return jsonify(service.create(data)), 201


@bp.get("")
def history():
    try:
        page = int(request.args.get("page", "1"))
    except ValueError:
        raise AppError("Página inválida.")
    status = request.args.get("status", "")
    if page < 1 or status not in ("", "pending", "completed"):
        raise AppError("Filtro de histórico inválido.")
    return jsonify(storage.list_incidents(request.args.get("q", "")[:200], status, page))


@bp.get("/<incident_id>")
def detail(incident_id):
    return jsonify(storage.get(incident_id))


@bp.post("/<incident_id>/triage")
def triage(incident_id):
    return jsonify(service.triage(incident_id))


@bp.patch("/<incident_id>/context")
def context(incident_id):
    return jsonify(storage.update_context(incident_id, UpdateContext.model_validate(request.get_json())))


@bp.post("/<incident_id>/review")
def review(incident_id):
    return jsonify(storage.save_review(incident_id, Review.model_validate(request.get_json())))


@bp.post("/<incident_id>/analyze")
def analyze(incident_id):
    return jsonify(service.analyze(incident_id))
