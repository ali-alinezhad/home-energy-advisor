from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.advice import AdviceResponse

HeatingType = Literal["gas", "oil", "electric", "heat_pump"]
InsulationLevel = Literal["low", "medium", "high"]
LAST_YEAR = datetime.now().year - 1


class HomeCreate(BaseModel):
    size: int = Field(..., ge=20, le=2000)
    year_built: int = Field(
        ...,
        ge=1800,
        le=LAST_YEAR,
        description="Year the home was built",
    )
    heating_type: HeatingType
    insulation_level: InsulationLevel


class HomeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    size: int
    year_built: int
    heating_type: HeatingType
    insulation_level: InsulationLevel
    latest_advice: Optional[AdviceResponse] = None
    advice_generated_at: Optional[datetime] = None
