from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

MAX_PWD = 256
MAX_STR = 500


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)
    id: uuid.UUID
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=MAX_PWD)
    full_name: str = Field(min_length=1, max_length=MAX_STR)


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, min_length=1, max_length=MAX_STR)
    password: str | None = Field(default=None, min_length=1, max_length=MAX_PWD)
    is_active: bool | None = None


class UserListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    items: list[UserOut]
    total: int
    skip: int
    limit: int
