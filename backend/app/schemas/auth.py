"""Authentication schemas."""

from typing import Literal

from pydantic import BaseModel, Field

Role = Literal["engineer", "customer"]


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=255)


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"]
    role: Role
