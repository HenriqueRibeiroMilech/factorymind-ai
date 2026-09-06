"""Reproducible, leakage-free comparison. Run outside Flask: python -m ml.src.train."""
import hashlib
import json
import platform
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, confusion_matrix, fbeta_score,
                             precision_score, recall_score)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[2]
SEED = 42
COLUMNS = {
    "Type": "product_type", "Air temperature [K]": "air_temperature",
    "Process temperature [K]": "process_temperature", "Rotational speed [rpm]": "rotational_speed",
    "Torque [Nm]": "torque", "Tool wear [min]": "tool_wear",
}
FEATURES = list(COLUMNS.values())
NUMERIC = FEATURES[1:]


def metrics(y, scores, threshold):
    predicted = scores >= threshold
    return {
        "precision": float(precision_score(y, predicted, zero_division=0)),
        "recall": float(recall_score(y, predicted, zero_division=0)),
        "f2": float(fbeta_score(y, predicted, beta=2, zero_division=0)),
        "average_precision": float(average_precision_score(y, scores)),
        "confusion_matrix": confusion_matrix(y, predicted, labels=[0, 1]).tolist(),
    }


def pipeline(classifier):
    preprocess = ColumnTransformer([
        ("type", OneHotEncoder(categories=[["L", "M", "H"]], handle_unknown="error", sparse_output=False), ["product_type"]),
        ("numeric", StandardScaler(), NUMERIC),
    ])
    return Pipeline([("preprocess", preprocess), ("classifier", classifier)])


def main():
    path = ROOT / "ml/data/ai4i2020.csv"
    if not path.is_file():
        raise SystemExit("Baixe os dados primeiro: python -m ml.src.download")
    df = pd.read_csv(path)
    if len(df) != 10000 or df.isna().any().any():
        raise SystemExit("O CSV não corresponde ao AI4I 2020 completo, sem ausências.")
    # Explicit allowlist: identifiers and every failure-mode column never enter X.
    X = df[list(COLUMNS)].rename(columns=COLUMNS)
    y = df["Machine failure"]
    X_train, X_holdout, y_train, y_holdout = train_test_split(X, y, test_size=0.4, stratify=y, random_state=SEED)
    X_val, X_test, y_val, y_test = train_test_split(X_holdout, y_holdout, test_size=0.5, stratify=y_holdout, random_state=SEED)
    estimators = {
        "baseline": DummyClassifier(strategy="prior", random_state=SEED),
        "logistic_regression": LogisticRegression(class_weight="balanced", max_iter=2000, random_state=SEED),
        "random_forest": RandomForestClassifier(n_estimators=300, max_depth=12, min_samples_leaf=2,
                                                class_weight="balanced_subsample", random_state=SEED, n_jobs=1),
    }
    fitted, results = {}, {}
    for name, estimator in estimators.items():
        model = pipeline(estimator)
        model.fit(X_train, y_train)
        scores = model.predict_proba(X_val)[:, 1]
        # F2 prioritizes recall on a rare-failure dataset. Precision breaks ties.
        # The baseline retains the conventional 0.5 threshold for a meaningful reference.
        candidates = [0.5] if name == "baseline" else np.round(np.arange(0.05, 0.96, 0.01), 2)
        threshold = max(candidates, key=lambda t: (metrics(y_val, scores, t)["f2"], metrics(y_val, scores, t)["precision"], float(t)))
        results[name] = {"threshold": float(threshold), "validation": metrics(y_val, scores, threshold)}
        fitted[name] = model
    selected = max(results, key=lambda name: (results[name]["validation"]["f2"], results[name]["validation"]["precision"]))
    # Selection is frozen above. Test is inspected exactly here, after model/threshold selection.
    for name, model in fitted.items():
        results[name]["test"] = metrics(y_test, model.predict_proba(X_test)[:, 1], results[name]["threshold"])

    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    artifacts = ROOT / "ml/artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    joblib.dump(fitted[selected], artifacts / "pipeline.joblib", compress=3)
    eda = {
        "rows": len(df), "columns": len(df.columns), "missing_values": int(df.isna().sum().sum()),
        "target_counts": {str(k): int(v) for k, v in y.value_counts().sort_index().items()},
        "failure_rate": float(y.mean()), "product_counts": X["product_type"].value_counts().to_dict(),
        "numeric_summary": X[NUMERIC].describe().round(4).to_dict(),
        "correlation_with_target": X[NUMERIC].corrwith(y).round(4).to_dict(),
        "failure_rate_by_type": pd.DataFrame({"type": X.product_type, "failure": y}).groupby("type")["failure"].mean().to_dict(),
    }
    metadata = {
        "version": f"ai4i-{selected}-v1-{digest[:10]}", "selected_model": selected,
        "threshold": results[selected]["threshold"], "features": FEATURES,
        "dataset_sha256": digest, "pipeline_sha256": hashlib.sha256((artifacts / "pipeline.joblib").read_bytes()).hexdigest(),
        "source": "https://doi.org/10.24432/C5HS5C", "seed": SEED,
        "split": {"train": len(X_train), "validation": len(X_val), "test": len(X_test)},
        "positive_counts": {"train": int(y_train.sum()), "validation": int(y_val.sum()), "test": int(y_test.sum())},
        "selection": "Maximum validation F2 over thresholds 0.05..0.95 (step 0.01); precision then higher threshold break ties. Baseline fixed at 0.5.",
        "training_ranges": {column: {"min": float(X_train[column].min()), "max": float(X_train[column].max())} for column in NUMERIC},
        "python_version": platform.python_version(), "sklearn_version": sklearn.__version__,
        "test_metrics": results[selected]["test"],
        "limitation": "Dataset sintético. Escore não calibrado de classificação da condição informada; não estima data de quebra nem descarta sintomas fora das variáveis.",
    }
    for filename, data in (("metadata.json", metadata), ("evaluation.json", results), ("eda.json", eda)):
        (artifacts / filename).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    write_note(metadata, results, eda)
    print(json.dumps({"selected": selected, "threshold": metadata["threshold"], "test": metadata["test_metrics"]}, indent=2))


def write_note(metadata, results, eda):
    table = "\n".join(
        f"| {name} | {row['threshold']:.2f} | {row['validation']['f2']:.4f} | {row['test']['precision']:.4f} | {row['test']['recall']:.4f} | {row['test']['f2']:.4f} |"
        for name, row in results.items()
    )
    matrix = metadata["test_metrics"]["confusion_matrix"]
    note = f"""# Avaliação do modelo de equipamentos

Fonte: [AI4I 2020, UCI](https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset), DOI [10.24432/C5HS5C](https://doi.org/10.24432/C5HS5C), licença CC BY 4.0. Dataset **sintético**, de manutenção preditiva, com {eda['rows']:,} registros e {eda['columns']} colunas. Download: `python -m ml.src.download`. Treino: `python -m ml.src.train`, na raiz do projeto, com as dependências fixadas do backend.

## Exploração objetiva

Sem valores ausentes. Há {eda['target_counts']['1']} falhas ({eda['failure_rate']:.2%}) e {eda['target_counts']['0']} condições sem falha: acurácia isolada seria enganosa. Tipos de produto: {eda['product_counts']}. Estatísticas de cada leitura, correlações e taxa de falha por tipo estão em [eda.json](artifacts/eda.json). Temperaturas e outras variáveis têm escalas diferentes; o pipeline padroniza as numéricas e codifica o tipo com one-hot.

## Estratégia e resultado

Alvo: `Machine failure`. Somente tipo, temperatura do ar, temperatura do processo, rotação, torque e desgaste entram no treino. UDI, Product ID e indicadores TWF/HDF/PWF/OSF/RNF são excluídos por seleção explícita das seis entradas. Vibração não existe como feature.

Separação aleatória estratificada 60/20/20, seed {SEED}: {metadata['split']}; positivos: {metadata['positive_counts']}. Pré-processamento ajustado **somente no treino**. Comparamos uma referência que sempre escolhe a classe majoritária, regressão logística balanceada e Random Forest balanceada. Modelos e limiares são escolhidos pela maior F2 na validação, priorizando recall; precisão e depois limiar maior desempataram. Busca de 0,05 a 0,95 com passo 0,01; referência mantida em 0,50. Hiperparâmetros fixos no script, sem busca no teste. O pipeline final permanece ajustado apenas nos 60% de treino; não há novo ajuste com validação ou teste.

| Classificador | Limiar | F2 validação | Precisão teste | Recall teste | F2 teste |
|---|---:|---:|---:|---:|---:|
{table}

Selecionado: **{metadata['selected_model']}**, limiar **{metadata['threshold']:.2f}**. Matriz de confusão do teste (linhas = real, colunas = predito, ordem sem falha / falha):

| | Predito sem falha | Predito falha |
|---|---:|---:|
| Real sem falha | {matrix[0][0]} | {matrix[0][1]} |
| Real falha | {matrix[1][0]} | {matrix[1][1]} |

Detalhes de todos os candidatos em [evaluation.json](artifacts/evaluation.json). [metadata.json](artifacts/metadata.json) guarda versão, limiar, faixas de treino, hash do CSV e do pipeline, bibliotecas e métricas. `pipeline.joblib` é gerado localmente e ignorado pelo Git; o servidor nunca treina. SHA256 do CSV: `{metadata['dataset_sha256']}`.

## Limites

O split aleatório mede desempenho dentro deste dataset sintético, com temperaturas correlacionadas e modos de falha construídos. Não comprova generalização temporal nem desempenho em uma fábrica real. A aplicação usa `predict_proba` como **escore não calibrado**, não como probabilidade garantida de falha. A decisão classifica a condição das seis leituras simultâneas; não estima quando ocorrerá uma quebra. Uma pontuação baixa pode coexistir com vibração, ruído ou outros sintomas ausentes do dataset. Leituras fora das faixas do treino aparecem como ressalva no relatório. Procedimentos fictícios e análise de LLM precisam de avaliação humana.
"""
    (ROOT / "ml/ML.md").write_text(note, encoding="utf-8")


if __name__ == "__main__":
    main()
