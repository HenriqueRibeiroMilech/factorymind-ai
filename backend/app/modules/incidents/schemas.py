from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.predictions.schemas import Measurements

Category = Literal["equipment", "quality", "processes"]


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CreateIncident(InputModel):
    request_id: UUID
    description: str = Field(min_length=10, max_length=5000)
    reference: str = Field(default="", max_length=160)
    relevant_risk: bool = Field(default=False, strict=True)


class UpdateContext(InputModel):
    complement: str = Field(default="", max_length=5000)
    measurements: Measurements | None = None


class Review(InputModel):
    category: Category
    justification: str = Field(min_length=8, max_length=1500)


class TriageAnswer(BaseModel):
    model_config = ConfigDict(extra="ignore", allow_inf_nan=False, strict=True)
    type: Literal["choice"]
    choice: Category
    confidence: float | None = Field(default=None, ge=0, le=1)


CATEGORIES = {
    "equipment": {"label": "Produção e equipamentos", "area": "Produção e manutenção de equipamentos"},
    "quality": {"label": "Qualidade", "area": "Qualidade"},
    "processes": {"label": "Processos industriais", "area": "Engenharia de processos"},
}
