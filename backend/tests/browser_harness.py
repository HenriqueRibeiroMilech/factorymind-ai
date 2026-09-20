"""Isolated browser-test server. Mocks exist only here, never in product config.

Run from the project root: python backend/tests/browser_harness.py
Uses an ephemeral SQLite database, real retrieval and real trained ML.
"""
import argparse
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app

CASES = {
    "A mesa da fresadora vibrou durante a segunda passada.": ("equipment", 0.94),
    # Intentionally wrong suggestion to exercise human correction in the browser.
    "O diâmetro das peças do lote está fora da tolerância.": ("equipment", 0.3),
    "As peças estão formando fila entre a usinagem e a inspeção.": ("processes", 0.92),
}


def classify(incident):
    category, confidence = CASES[incident["description"]]
    return {"category": category, "confidence": confidence, "model": "jev-browser-test"}


def generate(incident, sources, ml):
    supported = [sources[0]["id"]] if sources else []
    texts = {
        "equipment": ("O operador relata vibração durante a usinagem. A classificação das leituras não descarta esse sintoma, pois vibração não é uma entrada do modelo.",
                      "A condição de fixação é uma hipótese que exige inspeção pela equipe autorizada.",
                      "Encaminhar o relato a Produção e manutenção e registrar as condições observadas."),
        "quality": ("O defeito relatado é dimensional. A análise inicial deve permanecer em Qualidade; a causa física ainda precisa ser investigada.",
                    "Uma condição inadequada de medição é uma hipótese a verificar, sem conclusão sobre a causa.",
                    "Confirmar o desenho aprovado, o instrumento e a rastreabilidade antes de qualquer decisão sobre o lote."),
        "processes": ("A fila relatada sugere uma dificuldade no fluxo que precisa ser observada em campo antes de confirmar um gargalo permanente.",
                      "Desequilíbrio de capacidade entre etapas é uma hipótese a verificar com tempos e condições da operação.",
                      "Registrar as etapas e observar os tempos do fluxo com Engenharia de processos."),
    }
    analysis, hypothesis, recommendation = texts[incident["category"]]
    return {"initial_analysis": analysis,
            "hypotheses": [{"text": hypothesis, "source_ids": supported}],
            "recommendations": [{"text": recommendation, "source_ids": supported}],
            "missing_information": ["Solicitar histórico e condições da operação à equipe."], "review_needed": True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Isolated FactoryMind browser test server")
    parser.add_argument("--port", type=int, default=5001)
    args = parser.parse_args()
    with TemporaryDirectory(prefix="factorymind-browser-test-") as directory:
        app = create_app({"TESTING": True, "DATABASE_PATH": str(Path(directory) / "test.sqlite3"),
                          "JEV_API_KEY": "", "OPENAI_API_KEY": "", "LLM_MODEL": "llm-browser-test"})
        print("BROWSER TEST ONLY: isolated database, simulated providers, real retrieval and ML.")
        with patch("app.integrations.jev.classify", classify), patch("app.integrations.llm.generate", generate):
            app.run(host="127.0.0.1", port=args.port, debug=False, use_reloader=False)
