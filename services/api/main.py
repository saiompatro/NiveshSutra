"""Compatibility ASGI entrypoint for Render services using the old path.

The production FastAPI app lives in backend.main. Some Render services may
still have a Dashboard start command such as `uvicorn services.api.main:app`.
Keeping this bridge prevents those deployments from failing while render.yaml
uses the canonical `backend.main:app` entrypoint.
"""

from backend.main import app

__all__ = ["app"]
