from typing import Annotated

from fastapi import APIRouter, Cookie, Response, status

from app.core.auth import SESSION_COOKIE, ClockDep, CurrentUser, session_ttl
from app.core.config import get_settings
from app.core.db import SessionDep
from app.schemas.auth import LoginRequest, RegisterRequest, UserRead
from app.schemas.errors import error_responses
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=int(session_ttl().total_seconds()),
        httponly=True,
        secure=get_settings().cookie_secure,
        samesite="lax",
        path="/",
    )


@router.post(
    "/register", status_code=status.HTTP_201_CREATED, responses=error_responses(400, 403, 422)
)
def register(
    body: RegisterRequest, response: Response, session: SessionDep, clock: ClockDep
) -> UserRead:
    now = clock.now()
    user = auth_service.register(session, body, now=now)
    token = auth_service.create_session(session, user, now=now, ttl=session_ttl())
    _set_session_cookie(response, token)
    return UserRead.model_validate(user)


@router.post("/login", responses=error_responses(401, 403, 422, 429))
def login(body: LoginRequest, response: Response, session: SessionDep, clock: ClockDep) -> UserRead:
    now = clock.now()
    user = auth_service.authenticate(session, body, now=now)
    token = auth_service.create_session(session, user, now=now, ttl=session_ttl())
    _set_session_cookie(response, token)
    return UserRead.model_validate(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, responses=error_responses(403))
def logout(
    response: Response,
    session: SessionDep,
    habitude_session: Annotated[str | None, Cookie()] = None,
) -> None:
    auth_service.logout(session, habitude_session)
    response.delete_cookie(
        SESSION_COOKIE,
        path="/",
        httponly=True,
        secure=get_settings().cookie_secure,
        samesite="lax",
    )


@router.get("/me", responses=error_responses(401))
def me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)
