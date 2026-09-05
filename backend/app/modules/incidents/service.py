from flask import current_app

from app.errors import AppError
from app.integrations import jev, llm
from app.modules.incidents import storage
from app.modules.incidents.knowledge import retrieve
from app.modules.incidents.report import assemble
from app.modules.predictions.predictor import predict


def triage(incident_id):
    token = storage.claim(incident_id, "triaging")
    try:
        incident = storage.get(incident_id)
        result = jev.classify(incident)
        needs_review = (incident["relevant_risk"] or result["confidence"] is None
                        or result["confidence"] < current_app.config["REVIEW_THRESHOLD"])
        storage.finish(incident_id, token, suggested_category=result["category"], category=result["category"],
                       confidence=result["confidence"], jev_model=result["model"],
                       status="review_required" if needs_review else "ready")
    except AppError as exc:
        storage.finish(incident_id, token, status="triage_failed", last_error={"code": exc.code, "message": exc.message})
    except Exception:
        current_app.logger.exception("Triage failed unexpectedly")
        storage.finish(incident_id, token, status="triage_failed", last_error={"code": "triage_error", "message": "Não foi possível classificar. Seus dados estão salvos; tente novamente."})
    return storage.get(incident_id)


def create(data):
    incident = storage.create(data)
    if incident["status"] == "pending_triage":
        return triage(incident["id"])
    return incident


def analyze(incident_id):
    incident = storage.get(incident_id)
    if incident["status"] == "completed":
        return incident
    token = storage.claim(incident_id, "analyzing")
    try:
        # Read after claim: edits are now locked, so this is one consistent snapshot.
        incident = storage.get(incident_id)
        sources = retrieve(incident["category"], incident["description"] + " " + incident["complement"])
        if incident["category"] != "equipment":
            ml_result = {"status": "not_applicable", "limitation": "O modelo de equipamentos não se aplica a esta categoria."}
        elif not incident["measurements"]:
            ml_result = {"status": "missing_readings", "limitation": "Sem as seis medições simultâneas, o modelo de equipamentos não foi executado. O relato continua relevante."}
        else:
            ml_result = predict(incident["measurements"])
        raw = llm.generate(incident, sources, ml_result)
        report = assemble(incident, raw, sources, ml_result)
        report["llm_model"] = current_app.config["LLM_MODEL"]
        storage.finish(incident_id, token, status="completed", report=report)
    except AppError as exc:
        storage.finish(incident_id, token, status="analysis_failed", last_error={"code": exc.code, "message": exc.message})
    except Exception:
        current_app.logger.exception("Analysis failed unexpectedly")
        storage.finish(incident_id, token, status="analysis_failed", last_error={"code": "analysis_error", "message": "Não foi possível analisar. Seus dados estão salvos; tente novamente."})
    return storage.get(incident_id)
