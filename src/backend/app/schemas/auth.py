import re
from datetime import datetime
from typing import Annotated
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from app.core.security import normalize_email

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _valid_email(value: str) -> str:
    email = normalize_email(value)
    if len(email) > 254 or not _EMAIL_RE.match(email):
        raise ValueError("must be a valid email address")
    return email


def _valid_timezone(value: str) -> str:
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError("must be an IANA timezone name") from exc
    return value


Email = Annotated[str, AfterValidator(_valid_email)]
Timezone = Annotated[str, Field(max_length=64), AfterValidator(_valid_timezone)]


class RegisterRequest(BaseModel):
    email: Email
    password: str = Field(min_length=10, max_length=128)
    timezone: Timezone = "UTC"


class LoginRequest(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=128)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    timezone: str
    created_at: datetime
