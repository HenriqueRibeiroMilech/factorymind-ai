import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import train_test_split

from app.errors import AppError
from app.modules.predictions.predictor import load_model, predict
from test_analysis import READINGS

ROOT = Path(__file__).resolve().parents[2]
TRAINED = (ROOT / "ml/artifacts/pipeline.joblib").is_file() and (ROOT / "ml/data/ai4i2020.csv").is_file()


def test_missing_model_is_actionable(app, tmp_path):
    app.config["MODEL_DIR"] = str(tmp_path / "missing")
    with app.app_context(), pytest.raises(AppError, match="ml.src.train") as error:
        predict(READINGS)
    assert error.value.code == "model_unavailable"


@pytest.mark.skipif(not TRAINED, reason="Execute download e treino para testar o artefato real.")
def test_real_pipeline_has_only_six_features_and_train_only_scaler(app):
    from ml.src.train import COLUMNS, NUMERIC, SEED
    metadata = json.loads((ROOT / "ml/artifacts/metadata.json").read_text(encoding="utf-8"))
    model, _ = load_model(str(ROOT / "ml/artifacts"), 0, 0)
    df = pd.read_csv(ROOT / "ml/data/ai4i2020.csv")
    X = df[list(COLUMNS)].rename(columns=COLUMNS)
    y = df["Machine failure"]
    train, holdout, y_train, y_holdout = train_test_split(X, y, test_size=0.4, stratify=y, random_state=SEED)
    _, test, _, y_test = train_test_split(holdout, y_holdout, test_size=0.5, stratify=y_holdout, random_state=SEED)
    assert list(model.feature_names_in_) == list(COLUMNS.values())
    scaler = model.named_steps["preprocess"].named_transformers_["numeric"]
    np.testing.assert_allclose(scaler.mean_, train[NUMERIC].mean().to_numpy())
    assert scaler.n_samples_seen_ == 6000
    predictions = model.predict_proba(test)[:, 1] >= metadata["threshold"]
    assert confusion_matrix(y_test, predictions).tolist() == metadata["test_metrics"]["confusion_matrix"]
    with app.app_context():
        result = predict(READINGS)
    assert result["inputs"] == READINGS
    assert result["version"] == metadata["version"]
    assert result["threshold"] == metadata["threshold"]
    assert 0 <= result["score"] <= 1
    with app.app_context():
        outside = predict({**READINGS, "air_temperature": 700.0})
    assert any(warning["field"] == "air_temperature" for warning in outside["out_of_range"])


@pytest.mark.skipif(not TRAINED, reason="Execute download e treino para testar o artefato real.")
def test_real_ml_reaches_saved_report(client, monkeypatch):
    from test_analysis import mock_llm, setup_incident
    record = setup_incident(client, monkeypatch)
    mock_llm(monkeypatch)
    client.patch(f'/api/v1/incidents/{record["id"]}/context', json={"measurements": READINGS})
    result = client.post(f'/api/v1/incidents/{record["id"]}/analyze').json
    assert result["status"] == "completed"
    assert result["report"]["ml"]["status"] == "available"
    assert result["report"]["ml"]["version"].startswith("ai4i-random_forest-v1-")
