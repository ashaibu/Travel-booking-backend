from pydantic import BaseModel, EmailStr, Field
from typing import Literal


class UserCreate(BaseModel):
    full_name: str = Field(min_length=2)
    email: EmailStr
    password: str = Field(min_length=8)


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2)
    email: EmailStr | None = None
    role: Literal["user", "admin"] | None = None
    is_active: bool | None = None