import hashlib
import json
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd
import sklearn
from flask import current_app

from app.errors import AppError
from app.modules.predictions.schemas import Measurements


@lru_cache(maxsize=2)
def load_model(directory, pipeline_stamp, metadata_stamp):
    """Only load the locally trained, hash-matched artifact; never untrusted uploads."""
    directory = Path(directory)
    metadata = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
    digest = hashlib.sha256((directory / "pipeline.joblib").read_bytes()).hexdigest()
    if digest != metadata["pipeline_sha256"] or metadata["sklearn_version"] != sklearn.__version__:
        raise ValueError("Artifact mismatch: retrain with installed dependencies")
    if set(metadata["features"]) != set(Measurements.model_fields):
        raise ValueError("Unexpected model features")
    return joblib.load(directory / "pipeline.joblib"), metadata


def predict(measurements):
    directory = Path(current_app.config["MODEL_DIR"])
    try:
        model, metadata = load_model(str(directory), (directory / "pipeline.joblib").stat().st_mtime_ns,
                                    (directory / "metadata.json").stat().st_mtime_ns)
        inputs = Measurements.model_validate(measurements).model_dump()
        frame = pd.DataFrame([inputs], columns=metadata["features"])
        score = float(model.predict_proba(frame)[0, 1])
        threshold = metadata["threshold"]
        warnings = []
        for name, bounds in metadata["training_ranges"].items():
            if not bounds["min"] <= inputs[name] <= bounds["max"]:
                warnings.append({"field": name, "training_min": bounds["min"], "training_max": bounds["max"]})
        return {"status": "available", "inputs": inputs, "score": score, "threshold": threshold,
                "decision": "failure" if score >= threshold else "no_failure",
                "version": metadata["version"], "out_of_range": warnings,
                "limitation": metadata["limitation"]}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise AppError("O modelo treinado está ausente ou incompatível. Execute python -m ml.src.download e python -m ml.src.train na raiz do projeto e tente novamente.", "model_unavailable", 503) from exc
