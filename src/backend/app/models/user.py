from datetime import datetime

from sqlmodel import Column, Field, SQLModel

from app.core.db import UTCDateTime
from app.core.ids import new_id


class User(SQLModel, table=True):
    id: str = Field(default_factory=new_id, primary_key=True)
    email: str = Field(max_length=254, unique=True, index=True)
    password_hash: str
    timezone: str = Field(default="UTC", max_length=64)
    created_at: datetime = Field(sa_column=Column(UTCDateTime(), nullable=False))
