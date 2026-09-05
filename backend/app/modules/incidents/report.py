import re

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.errors import ProviderError
from app.modules.incidents.schemas import CATEGORIES
from app.modules.incidents.storage import now


class Finding(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    text: str = Field(min_length=8, max_length=1800)
    source_ids: list[str] = Field(max_length=4)


class Narrative(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    initial_analysis: str = Field(min_length=20, max_length=4000)
    hypotheses: list[Finding] = Field(max_length=6)
    recommendations: list[Finding] = Field(max_length=8)
    missing_information: list[str] = Field(max_length=12)
    review_needed: bool = Field(strict=True)


def assemble(incident, raw, sources, ml):
    """Facts and numeric fields are copied from their sources, never accepted from the LLM."""
    try:
        narrative = Narrative.model_validate(raw)
        allowed = {source["id"] for source in sources}
        for finding in narrative.hypotheses + narrative.recommendations:
            if len(set(finding.source_ids)) != len(finding.source_ids) or not set(finding.source_ids) <= allowed:
                raise ValueError("Unknown or duplicate citation")
        texts = [narrative.initial_analysis, *narrative.missing_information,
                 *(finding.text for finding in narrative.hypotheses + narrative.recommendations)]
        # Numeric information has dedicated canonical fields. This prevents invented/repeated
        # scores, limits, measurements and dates from entering generated prose.
        if any(re.search(r"\d", text) for text in texts):
            raise ValueError("Numeric claims belong in canonical fields")
    except (ValidationError, ValueError, TypeError) as exc:
        raise ProviderError("O LLM devolveu um relatório inválido ou com fontes/valores inconsistentes. Seus dados estão salvos; tente a análise novamente.", "invalid_report", 502) from exc

    gaps = []
    if not sources:
        gaps.append("Não foram encontrados trechos relevantes no acervo desta área.")
    for label, findings in (("Hipótese", narrative.hypotheses), ("Recomendação", narrative.recommendations)):
        for index, finding in enumerate(findings, 1):
            if not finding.source_ids:
                gaps.append(f"{label} {index}: sem apoio documental no contexto recuperado; requer avaliação humana.")
    if ml["status"] == "missing_readings":
        gaps.append(ml["limitation"])
    if ml.get("out_of_range"):
        gaps.append("Há medições fora das faixas observadas no treino. Avaliar a extrapolação com a equipe.")
    return {
        "incident_id": incident["id"], "generated_at": now(),
        "original_description": incident["description"], "complement": incident["complement"],
        "reference": incident["reference"], "relevant_risk": incident["relevant_risk"],
        "category": incident["category"], "category_label": CATEGORIES[incident["category"]]["label"],
        "responsible_area": CATEGORIES[incident["category"]]["area"],
        "triage": {"suggested_category": incident["suggested_category"], "confidence": incident["confidence"], "model": incident["jev_model"]},
        "human_review": incident["review"], **narrative.model_dump(),
        "ml": ml, "sources": sources, "evidence_gaps": gaps,
        "review_needed": bool(narrative.review_needed or gaps or incident["relevant_risk"]),
        "notice": "Análise inicial assistida por IA. Procedimentos fictícios para portfólio; confira os trechos e valide as hipóteses antes de qualquer decisão operacional.",
    }
