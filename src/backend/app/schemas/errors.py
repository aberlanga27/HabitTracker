from typing import Any

from pydantic import BaseModel


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any]


class ErrorEnvelope(BaseModel):
    error: ErrorBody


def error_responses(*status_codes: int) -> dict[int | str, dict[str, Any]]:
    """OpenAPI `responses=` entries documenting the error envelope for each status code."""
    return {code: {"model": ErrorEnvelope} for code in status_codes}
