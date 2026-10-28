from typing import Literal

from pydantic import BaseModel, Field

from .config import settings


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1, max_length=16000)


class GenerateRequest(BaseModel):
    messages: list[Message] = Field(min_length=1, max_length=50)
    temperature: float = Field(default=settings.default_temperature, ge=0, le=2)
    top_p: float = Field(default=settings.default_top_p, gt=0, le=1)
    top_k: int = Field(default=settings.default_top_k, ge=1, le=256)
    max_tokens: int = Field(default=settings.default_max_tokens, ge=1, le=4096)


class GenerateResponse(BaseModel):
    response: str
    queue_position: int
