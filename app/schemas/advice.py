from typing import Literal

from pydantic import BaseModel, Field


class Recommendation(BaseModel):
    title: str = Field(..., min_length=3, max_length=120)
    description: str = Field(..., min_length=10, max_length=500)
    priority: Literal["high", "medium", "low"]


class AdviceResponse(BaseModel):
    recommendations: list[Recommendation] = Field(
        ..., min_length=3, max_length=3
    )
