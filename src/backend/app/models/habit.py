from datetime import datetime

from sqlmodel import Column, Field, SQLModel

from app.core.db import UTCDateTime
from app.core.ids import new_id


class Habit(SQLModel, table=True):
    id: str = Field(default_factory=new_id, primary_key=True)
    user_id: str = Field(foreign_key="user.id", index=True, ondelete="CASCADE")
    name: str = Field(max_length=80)
    description: str | None = Field(default=None, max_length=500)
    icon: str | None = Field(default=None, max_length=16)
    color: str = Field(default="coral", max_length=16)
    position: int = 0
    archived_at: datetime | None = Field(default=None, sa_column=Column(UTCDateTime()))
    created_at: datetime = Field(sa_column=Column(UTCDateTime(), nullable=False))
