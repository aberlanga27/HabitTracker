"""CSRF defense: state-changing API requests must carry `X-Requested-With`."""

from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.errors import error_response

_UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


class RequireRequestedWithMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if (
            scope["type"] == "http"
            and scope["method"] in _UNSAFE_METHODS
            and scope["path"].startswith("/api/")
            and not any(name == b"x-requested-with" for name, _ in scope["headers"])
        ):
            response = error_response(403, "FORBIDDEN", "Missing X-Requested-With header")
            await response(scope, receive, send)
            return
        await self.app(scope, receive, send)
