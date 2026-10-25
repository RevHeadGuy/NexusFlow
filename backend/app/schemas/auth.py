from datetime import datetime
import re

from pydantic import BaseModel, Field, field_validator


def _normalize_email(value: str) -> str:
    value = value.strip().lower()
    if len(value) > 320 or not re.fullmatch(r"[^@\s]+@[^@\s.]+(?:\.[^@\s.]+)+", value):
        raise ValueError("Enter a valid email address.")
    return value


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    display_name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=10, max_length=128)

    @field_validator("display_name")
    @classmethod
    def clean_display_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Display name cannot be blank.")
        return cleaned

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return _normalize_email(value)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return _normalize_email(value)


class UserRead(BaseModel):
    id: str
    email: str
    display_name: str
    created_at: datetime


class TokenRead(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserRead


class InviteCreate(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    role: str = Field(pattern="^(editor|reviewer|viewer)$")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return _normalize_email(value)


class InviteAccept(BaseModel):
    token: str = Field(min_length=32, max_length=128)


class MemberRead(BaseModel):
    user_id: str
    email: str
    display_name: str
    role: str
    created_at: datetime


class InvitationRead(BaseModel):
    id: str
    project_id: str
    email: str
    role: str
    expires_at: datetime
    invite_token: str | None = None
    # True when an invitation email was actually sent (email delivery enabled
    # and SMTP reachable). False means the inviter should share the link manually.
    email_sent: bool = False
