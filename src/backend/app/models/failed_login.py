from datetime import datetime

from sqlmodel import Column, Field, SQLModel

from app.core.db import UTCDateTime
from app.core.ids import new_id


class FailedLogin(SQLModel, table=True):
    __tablename__ = "failed_login"

    id: str = Field(default_factory=new_id, primary_key=True)
    email: str = Field(max_length=254, index=True)
    attempted_at: datetime = Field(sa_column=Column(UTCDateTime(), nullable=False))
