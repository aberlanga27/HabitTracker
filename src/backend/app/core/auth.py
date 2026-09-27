"""Current-user dependency backed by the session cookie."""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Annotated

from fastapi import Cookie, Depends

from app.core.clock import Clock, get_clock, local_date
from app.core.config import get_settings
from app.core.db import SessionDep
from app.models import User
from app.services import auth as auth_service

SESSION_COOKIE = "habitude_session"

ClockDep = Annotated[Clock, Depends(get_clock)]


def session_ttl() -> timedelta:
    return timedelta(days=get_settings().session_ttl_days)


def get_current_user(
    session: SessionDep,
    clock: ClockDep,
    habitude_session: Annotated[str | None, Cookie()] = None,
) -> User:
    return auth_service.resolve_session(
        session, habitude_session, now=clock.now(), ttl=session_ttl()
    )


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_today(user: CurrentUser, clock: ClockDep) -> date:
    """The current user's local calendar date."""
    return local_date(clock.now(), user.timezone)


TodayDep = Annotated[date, Depends(get_today)]


@dataclass(frozen=True)
class Viewer:
    """Who is asking and what their local calendar looks like right now."""

    user_id: str
    timezone: str
    today: date


def get_viewer(user: CurrentUser, today: TodayDep) -> Viewer:
    return Viewer(user_id=user.id, timezone=user.timezone, today=today)


ViewerDep = Annotated[Viewer, Depends(get_viewer)]
