from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Measurements(BaseModel):
    """Six simultaneous readings. Bounds check physical plausibility, not training coverage."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, strict=True)
    product_type: Literal["L", "M", "H"]
    air_temperature: float = Field(gt=0, le=1000)
    process_temperature: float = Field(gt=0, le=1500)
    rotational_speed: float = Field(gt=0, le=100000)
    torque: float = Field(gt=0, le=10000)
    tool_wear: float = Field(ge=0, le=100000)
