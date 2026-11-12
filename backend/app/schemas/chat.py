"""Chat schemas."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ChatQuery(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    session_id: str | None = Field(default=None, min_length=1, max_length=64)


class ChatResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str
    citations: list[str]
    warnings: list[str]
    confidence: Literal["high", "medium", "low"]
    tool_executed: str
    execution_time_ms: float
