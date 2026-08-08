import uuid
from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    phone: str | None = None
    password: str = Field(min_length=8)
    full_name: str
    role: UserRole = UserRole.USER
    district: str | None = None
    state: str | None = None
    language_pref: str = "en"


class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    phone: str | None
    full_name: str
    role: UserRole
    district: str | None
    state: str | None
    language_pref: str

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
