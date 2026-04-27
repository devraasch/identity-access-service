from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=500)


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshIn(BaseModel):
    refresh_token: str = Field(min_length=10, max_length=2000)


class RefreshOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class LogoutIn(BaseModel):
    refresh_token: str = Field(min_length=10, max_length=2000)
