from uuid import uuid4

from app.modules.incidents import storage


def payload(**changes):
    return {"request_id": str(uuid4()), "description": "A mesa da fresadora vibrou na segunda passada.", **changes}


def classify(monkeypatch, category="equipment", confidence=0.9):
    monkeypatch.setattr("app.integrations.jev.classify", lambda _: {"category": category, "confidence": confidence, "model": "jev-test"})


def test_missing_key_preserves_and_retries_same_id(client, monkeypatch):
    data = payload()
    response = client.post("/api/v1/incidents", json=data)
    assert response.status_code == 201
    record = response.json
    assert record["status"] == "triage_failed"
    assert record["last_error"]["code"] == "jev_not_configured"
    assert client.post("/api/v1/incidents", json=data).json["id"] == record["id"]
    classify(monkeypatch)
    retried = client.post(f'/api/v1/incidents/{record["id"]}/triage').json
    assert retried["id"] == record["id"]
    assert retried["status"] == "ready"
    assert client.get(f'/api/v1/incidents/{record["id"]}').json["description"] == data["description"]


def test_review_preserves_suggestion_and_original(client, monkeypatch):
    classify(monkeypatch, confidence=None)
    record = client.post("/api/v1/incidents", json=payload()).json
    assert record["status"] == "review_required"
    reviewed = client.post(f'/api/v1/incidents/{record["id"]}/review', json={"category": "quality", "justification": "O defeito observado é na peça."}).json
    assert reviewed["suggested_category"] == "equipment"
    assert reviewed["category"] == "quality"
    assert reviewed["review"]["justification"] == "O defeito observado é na peça."
    assert reviewed["status"] == "ready"


def test_risk_requires_review(client, monkeypatch):
    classify(monkeypatch)
    assert client.post("/api/v1/incidents", json=payload(relevant_risk=True)).json["status"] == "review_required"


def test_invalid_data_and_idempotency_conflict(client):
    assert client.post("/api/v1/incidents", json=payload(description=" ")).status_code == 422
    data = payload()
    client.post("/api/v1/incidents", json=data)
    assert client.post("/api/v1/incidents", json={**data, "description": "Um relato diferente para a mesma chave."}).status_code == 409


def test_crashed_request_is_resumable(app, client, monkeypatch):
    classify(monkeypatch)
    record = client.post("/api/v1/incidents", json=payload()).json
    with app.app_context():
        storage.claim(record["id"], "analyzing")
        with storage.connection() as db:
            db.execute("UPDATE incidents SET processing_since = ? WHERE id = ?", ("2000-01-01T00:00:00+00:00", record["id"]))
    recovered = client.get(f'/api/v1/incidents/{record["id"]}').json
    assert recovered["status"] == "analysis_failed"
    assert recovered["last_error"]["code"] == "interrupted"


def test_history_search_handles_portuguese_and_uppercase_ids(client, monkeypatch):
    classify(monkeypatch, category="quality")
    record = client.post("/api/v1/incidents", json=payload(description="O diâmetro da peça está fora da tolerância.", reference="Lote Ç-10")).json
    for query in ("DIÂMETRO", "LOTE Ç", record["id"][:8].upper()):
        result = client.get("/api/v1/incidents", query_string={"q": query, "status": "pending"}).json
        assert result["total"] == 1
        assert result["items"][0]["id"] == record["id"]
    assert client.get("/api/v1/incidents", query_string={"q": "' OR 1=1 --"}).json["total"] == 0
