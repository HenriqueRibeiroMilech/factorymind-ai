import json

import pytest
import requests

from app.errors import ProviderError
from app.integrations import jev, llm


class Response:
    def __init__(self, body, status=200):
        self.body, self.status_code = body, status

    def json(self):
        return self.body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError("test response")


def test_jev_http_contract_and_absent_confidence(app, monkeypatch):
    captured = {}
    def post(url, **kwargs):
        captured.update(url=url, **kwargs)
        return Response({"model": "jev-test", "answers": {"category": {"type": "choice", "choice": "quality"}}})
    monkeypatch.setattr(requests, "post", post)
    app.config["JEV_API_KEY"] = "test-key"
    with app.app_context():
        result = jev.classify({"description": "Diâmetro fora da tolerância", "reference": "Lote"})
    assert result["confidence"] is None
    assert result["category"] == "quality"
    assert captured["url"] == "https://api.typesafe.ai/v1/systemone"
    assert set(captured["json"]["questions"]["category"]["criteria"]) == {"equipment", "quality", "processes"}
    assert captured["headers"]["Authorization"] == "Bearer test-key"


@pytest.mark.parametrize("body", [None, {}, {"model": "jev", "answers": {"category": {"type": "choice", "choice": "other", "confidence": 1.0}}}, {"model": "jev", "answers": {"category": {"type": "choice", "choice": "quality", "confidence": 1.5}}}])
def test_jev_rejects_invalid_contract(app, monkeypatch, body):
    app.config["JEV_API_KEY"] = "test-key"
    monkeypatch.setattr(requests, "post", lambda *a, **k: Response(body))
    with app.app_context(), pytest.raises(ProviderError):
        jev.classify({"description": "Relato", "reference": ""})


def test_provider_timeout_and_authentication_are_clear(app, monkeypatch):
    app.config["JEV_API_KEY"] = "test-key"
    def timeout(*a, **k):
        raise requests.Timeout()
    monkeypatch.setattr(requests, "post", timeout)
    with app.app_context(), pytest.raises(ProviderError, match="salvo"):
        jev.classify({"description": "Relato", "reference": ""})
    monkeypatch.setattr(requests, "post", lambda *a, **k: Response({}, 401))
    with app.app_context(), pytest.raises(ProviderError, match="credencial"):
        jev.classify({"description": "Relato", "reference": ""})


def test_llm_structured_contract_uses_same_client_for_every_profile(app, monkeypatch):
    app.config["OPENAI_API_KEY"] = "test-key"
    captured = []
    def post(url, **kwargs):
        captured.append((url, kwargs))
        return Response({"choices": [{"finish_reason": "stop", "message": {"content": json.dumps({"ok": True})}}]})
    monkeypatch.setattr(requests, "post", post)
    for category in ("equipment", "quality", "processes"):
        incident = {"description": "Relato", "complement": "", "reference": "", "category": category, "relevant_risk": False}
        with app.app_context():
            assert llm.generate(incident, [], {"status": "not_applicable"}) == {"ok": True}
    assert len({url for url, kwargs in captured}) == 1
    assert len({kwargs["json"]["model"] for url, kwargs in captured}) == 1
    assert all(kwargs["json"]["response_format"]["json_schema"]["strict"] for url, kwargs in captured)
