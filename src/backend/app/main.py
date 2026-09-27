"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.csrf import RequireRequestedWithMiddleware
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging
from app.routers import auth, check_ins, habits

API_PREFIX = "/api/v1"


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    app = FastAPI(
        title="Habitude API",
        version="1",
        openapi_url=f"{API_PREFIX}/openapi.json",
        docs_url=f"{API_PREFIX}/docs",
        redoc_url=None,
    )
    app.add_middleware(RequireRequestedWithMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_error_handlers(app)
    app.include_router(auth.router, prefix=API_PREFIX)
    app.include_router(habits.router, prefix=API_PREFIX)
    app.include_router(check_ins.router, prefix=API_PREFIX)
    return app


app = create_app()
