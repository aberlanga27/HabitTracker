from datetime import datetime

from sqlmodel import Column, Field, SQLModel

from app.core.db import UTCDateTime
from app.core.ids import new_id


class AuthSession(SQLModel, table=True):
    __tablename__ = "auth_session"

    id: str = Field(default_factory=new_id, primary_key=True)
    user_id: str = Field(foreign_key="user.id", index=True, ondelete="CASCADE")
    token_hash: str = Field(unique=True, index=True)
    created_at: datetime = Field(sa_column=Column(UTCDateTime(), nullable=False))
    last_used_at: datetime = Field(sa_column=Column(UTCDateTime(), nullable=False))
    expires_at: datetime = Field(sa_column=Column(UTCDateTime(), nullable=False))
