import shutil
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from argon2 import PasswordHasher
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlmodel import Session

from app.core import security
from app.core.clock import get_clock
from app.core.db import build_engine, get_session
from app.main import create_app
from tests.fakes import FrozenClock

BACKEND_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def template_db(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A database migrated to Alembic head once; copied per test."""
    path = tmp_path_factory.mktemp("template") / "template.db"
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{path}")
    config.attributes["configure_logger"] = False
    command.upgrade(config, "head")
    return path


@pytest.fixture
def engine(template_db: Path, tmp_path: Path) -> Iterator[Engine]:
    path = tmp_path / "test.db"
    shutil.copyfile(template_db, path)
    engine = build_engine(f"sqlite:///{path}")
    yield engine
    engine.dispose()


@pytest.fixture
def db(engine: Engine) -> Iterator[Session]:
    with Session(engine) as session:
        yield session


@pytest.fixture
def clock() -> FrozenClock:
    return FrozenClock(datetime(2026, 9, 26, 12, 0, tzinfo=UTC))


@pytest.fixture(autouse=True)
def fast_password_hasher(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        security, "_hasher", PasswordHasher(time_cost=1, memory_cost=8, parallelism=1)
    )


@pytest.fixture
def app(engine: Engine, clock: FrozenClock) -> FastAPI:
    application = create_app()

    def _session() -> Iterator[Session]:
        with Session(engine) as session:
            yield session

    application.dependency_overrides[get_session] = _session
    application.dependency_overrides[get_clock] = lambda: clock
    return application


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app, headers={"X-Requested-With": "XMLHttpRequest"}) as test_client:
        yield test_client
