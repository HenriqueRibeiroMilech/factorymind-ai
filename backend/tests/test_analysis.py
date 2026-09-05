from copy import deepcopy

import pytest

from app import create_app
from app.modules.incidents import storage
from app.modules.incidents.knowledge import retrieve
from test_incidents import classify, payload

READINGS = {"product_type": "L", "air_temperature": 298.1, "process_temperature": 308.6,
            "rotational_speed": 1551.0, "torque": 42.8, "tool_wear": 0.0}


def narrative(sources):
    ids = [sources[0]["id"]] if sources else []
    return {"initial_analysis": "O relato registra uma condição que precisa ser verificada pela equipe da área.",
            "hypotheses": [{"text": "A condição de fixação é uma hipótese a verificar em campo.", "source_ids": ids}],
            "recommendations": [{"text": "Encaminhar a observação à equipe responsável para avaliação.", "source_ids": ids}],
            "missing_information": ["Solicitar histórico e condições da operação."], "review_needed": True}


def setup_incident(client, monkeypatch, category="equipment", **changes):
    classify(monkeypatch, category)
    return client.post("/api/v1/incidents", json=payload(**changes)).json


def mock_llm(monkeypatch):
    calls = []
    def generate(incident, sources, ml):
        calls.append((deepcopy(incident), deepcopy(sources), deepcopy(ml)))
        return narrative(sources)
    monkeypatch.setattr("app.integrations.llm.generate", generate)
    return calls


@pytest.mark.parametrize("category", ["quality", "processes"])
def test_ml_is_not_called_for_other_categories(client, monkeypatch, category):
    record = setup_incident(client, monkeypatch, category)
    calls = mock_llm(monkeypatch)
    def fail(_):
        pytest.fail("Equipment ML must not be called")
    monkeypatch.setattr("app.modules.incidents.service.predict", fail)
    result = client.post(f'/api/v1/incidents/{record["id"]}/analyze').json
    assert result["status"] == "completed"
    assert result["report"]["ml"]["status"] == "not_applicable"
    assert calls[0][2]["status"] == "not_applicable"


def test_missing_readings_and_persistent_report(app, client, monkeypatch):
    record = setup_incident(client, monkeypatch)
    calls = mock_llm(monkeypatch)
    updated = client.patch(f'/api/v1/incidents/{record["id"]}/context', json={"complement": "A vibração se repetiu após a pausa.", "measurements": None})
    assert updated.status_code == 200
    result = client.post(f'/api/v1/incidents/{record["id"]}/analyze').json
    assert result["status"] == "completed"
    report = result["report"]
    assert report["original_description"] == record["description"]
    assert report["complement"] == "A vibração se repetiu após a pausa."
    assert report["ml"]["status"] == "missing_readings"
    assert report["sources"] and report["sources"][0]["excerpt"]
    assert report["evidence_gaps"]
    # A completely new Flask instance must read the stored report, without another LLM call.
    reopened = create_app({"TESTING": True, "DATABASE_PATH": app.config["DATABASE_PATH"]}).test_client()
    assert reopened.get(f'/api/v1/incidents/{record["id"]}').json["report"] == report
    assert reopened.post(f'/api/v1/incidents/{record["id"]}/analyze').json["report"] == report
    assert len(calls) == 1
    assert client.patch(f'/api/v1/incidents/{record["id"]}/context', json={"complement": "Outra informação."}).status_code == 409


def test_equipment_uses_canonical_model_values(client, monkeypatch):
    record = setup_incident(client, monkeypatch)
    calls = mock_llm(monkeypatch)
    expected = {"status": "available", "inputs": READINGS, "score": 0.123456789, "threshold": 0.27,
                "decision": "no_failure", "version": "test-model-v1", "out_of_range": [], "limitation": "Sintético."}
    seen = []
    def predict(inputs):
        seen.append(inputs)
        return deepcopy(expected)
    monkeypatch.setattr("app.modules.incidents.service.predict", predict)
    assert client.patch(f'/api/v1/incidents/{record["id"]}/context', json={"complement": "", "measurements": READINGS}).status_code == 200
    result = client.post(f'/api/v1/incidents/{record["id"]}/analyze').json
    assert seen == [READINGS]
    assert calls[0][2] == expected
    assert result["report"]["ml"] == expected
    assert "vibrou" in result["report"]["original_description"]


@pytest.mark.parametrize("change", ["citation", "numeric", "extra_fact"])
def test_untrusted_report_is_rejected_and_can_retry(client, monkeypatch, change):
    record = setup_incident(client, monkeypatch)
    def invalid(incident, sources, ml):
        result = narrative(sources)
        if change == "citation":
            result["recommendations"][0]["source_ids"] = ["invented-document"]
        elif change == "numeric":
            result["initial_analysis"] = "O modelo aponta um escore de 99% sem falha."
        else:
            result["ml"] = {"score": 999}
        return result
    monkeypatch.setattr("app.integrations.llm.generate", invalid)
    result = client.post(f'/api/v1/incidents/{record["id"]}/analyze').json
    assert result["status"] == "analysis_failed"
    assert result["last_error"]["code"] == "invalid_report"
    assert result["report"] is None
    mock_llm(monkeypatch)
    assert client.post(f'/api/v1/incidents/{record["id"]}/analyze').json["status"] == "completed"


def test_document_gap_is_explicit(client, monkeypatch):
    record = setup_incident(client, monkeypatch, "quality")
    monkeypatch.setattr("app.modules.incidents.service.retrieve", lambda *args: [])
    mock_llm(monkeypatch)
    report = client.post(f'/api/v1/incidents/{record["id"]}/analyze').json["report"]
    assert report["sources"] == []
    assert len(report["evidence_gaps"]) == 3
    assert report["review_needed"] is True


def test_llm_failure_preserves_context_and_retries(client, monkeypatch):
    record = setup_incident(client, monkeypatch, "quality")
    client.patch(f'/api/v1/incidents/{record["id"]}/context', json={"complement": "Lote segregado para avaliação."})
    failed = client.post(f'/api/v1/incidents/{record["id"]}/analyze').json
    assert failed["status"] == "analysis_failed"
    assert failed["last_error"]["code"] == "llm_not_configured"
    assert failed["complement"] == "Lote segregado para avaliação."
    mock_llm(monkeypatch)
    result = client.post(f'/api/v1/incidents/{record["id"]}/analyze').json
    assert result["id"] == record["id"] and result["status"] == "completed"


def test_review_blocks_analysis_and_clears_inapplicable_readings(client, monkeypatch):
    classify(monkeypatch, confidence=0.2)
    record = client.post("/api/v1/incidents", json=payload()).json
    assert client.post(f'/api/v1/incidents/{record["id"]}/analyze').status_code == 409
    client.patch(f'/api/v1/incidents/{record["id"]}/context', json={"measurements": READINGS})
    reviewed = client.post(f'/api/v1/incidents/{record["id"]}/review', json={"category": "quality", "justification": "O problema observado foi um defeito da peça."}).json
    assert reviewed["measurements"] is None
    assert client.patch(f'/api/v1/incidents/{record["id"]}/context', json={"measurements": READINGS}).status_code == 422


def test_measurement_validation_and_busy_lock(app, client, monkeypatch):
    record = setup_incident(client, monkeypatch)
    for readings in ({"product_type": "L"}, {**READINGS, "torque": -1}, {**READINGS, "vibration": 5}, {**READINGS, "product_type": "X"}, {**READINGS, "torque": "42.8"}):
        assert client.patch(f'/api/v1/incidents/{record["id"]}/context', json={"measurements": readings}).status_code == 422
    with app.app_context():
        storage.claim(record["id"], "analyzing")
    assert client.post(f'/api/v1/incidents/{record["id"]}/analyze').status_code == 409
    assert client.post(f'/api/v1/incidents/{record["id"]}/review', json={"category": "quality", "justification": "Confirmação humana da categoria."}).status_code == 409


def test_sources_are_verbatim_and_area_specific(app):
    with app.app_context():
        sources = retrieve("quality", "diâmetro fora da tolerância")
    assert sources
    for source in sources:
        assert source["document"].startswith("quality/")
        assert len(source["excerpt"]) > 50
        from pathlib import Path
        original = Path(app.config["KNOWLEDGE_DIR"]) / source["document"]
        assert source["excerpt"] in original.read_text(encoding="utf-8")
    with app.app_context():
        assert retrieve("quality", "xyzxyzqabc") == []
