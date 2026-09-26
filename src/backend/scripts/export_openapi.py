"""Write the OpenAPI document to src/backend/openapi.json (the committed contract snapshot)."""

import json
from pathlib import Path

from app.main import create_app

SNAPSHOT = Path(__file__).resolve().parents[1] / "openapi.json"


def render() -> str:
    return json.dumps(create_app().openapi(), indent=2, sort_keys=True) + "\n"


if __name__ == "__main__":
    SNAPSHOT.write_text(render())
