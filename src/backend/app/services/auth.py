"""Account registration, sign-in with lockout, and session lifecycle (spec 001)."""

from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, delete, select

from app.core.errors import AppError, AuthError, LockedOutError
from app.core.logging import get_logger
from app.core.security import (
    burn_verification_time,
    hash_password,
    hash_token,
    new_session_token,
    normalize_email,
    verify_password,
)
from app.models import AuthSession, FailedLogin, User
from app.schemas.auth import LoginRequest, RegisterRequest

LOCKOUT_THRESHOLD = 5
LOCKOUT_WINDOW = timedelta(minutes=15)

logger = get_logger("auth")


class RegistrationFailedError(AppError):
    status_code = 400
    code = "REGISTRATION_FAILED"


class InvalidCredentialsError(AppError):
    status_code = 401
    code = "INVALID_CREDENTIALS"


def register(session: Session, data: RegisterRequest, *, now: datetime) -> User:
    """Create a user. Raises RegistrationFailedError without revealing why (FR-008)."""
    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        timezone=data.timezone,
        created_at=now,
    )
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise RegistrationFailedError("Could not register") from None
    session.refresh(user)
    logger.info("user registered", extra={"user_id": user.id})
    return user


def _is_locked_out(session: Session, email: str, now: datetime) -> bool:
    recent = session.exec(
        select(FailedLogin.attempted_at)
        .where(FailedLogin.email == email)
        .order_by(col(FailedLogin.attempted_at).desc())
        .limit(LOCKOUT_THRESHOLD)
    ).all()
    if len(recent) < LOCKOUT_THRESHOLD:
        return False
    latest, oldest = recent[0], recent[-1]
    return latest - oldest <= LOCKOUT_WINDOW and now - latest < LOCKOUT_WINDOW


def authenticate(session: Session, data: LoginRequest, *, now: datetime) -> User:
    """Verify credentials with per-email lockout (FR-007).

    Raises LockedOutError or InvalidCredentialsError.
    """
    email = normalize_email(data.email)
    if _is_locked_out(session, email, now):
        logger.warning("sign-in rejected: locked out")
        raise LockedOutError("Too many failed attempts. Try again in 15 minutes.")

    user = session.exec(select(User).where(User.email == email)).first()
    if user is None:
        burn_verification_time(data.password)
    if user is None or not verify_password(user.password_hash, data.password):
        session.add(FailedLogin(email=email, attempted_at=now))
        session.commit()
        raise InvalidCredentialsError("Invalid email or password")

    session.exec(delete(FailedLogin).where(col(FailedLogin.email) == email))
    session.commit()
    return user


def create_session(session: Session, user: User, *, now: datetime, ttl: timedelta) -> str:
    """Persist a new session and return the raw token for the cookie."""
    token = new_session_token()
    session.add(
        AuthSession(
            user_id=user.id,
            token_hash=hash_token(token),
            created_at=now,
            last_used_at=now,
            expires_at=now + ttl,
        )
    )
    session.commit()
    return token


def resolve_session(session: Session, token: str | None, *, now: datetime, ttl: timedelta) -> User:
    """Return the session's user and slide its expiry (FR-004). Raises AuthError."""
    if not token:
        raise AuthError("Not signed in")
    auth_session = session.exec(
        select(AuthSession).where(AuthSession.token_hash == hash_token(token))
    ).first()
    if auth_session is None:
        raise AuthError("Not signed in")
    if now >= auth_session.expires_at:
        session.delete(auth_session)
        session.commit()
        raise AuthError("Session expired")
    auth_session.last_used_at = now
    auth_session.expires_at = now + ttl
    session.add(auth_session)
    session.commit()
    user = session.get(User, auth_session.user_id)
    if user is None:
        raise AuthError("Not signed in")
    return user


def logout(session: Session, token: str | None) -> None:
    """Delete the session for `token` if it exists (FR-005)."""
    if not token:
        return
    session.exec(delete(AuthSession).where(col(AuthSession.token_hash) == hash_token(token)))
    session.commit()
