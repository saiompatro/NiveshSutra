"""Thin HTTP client for calling the separately hosted FastAPI service."""

from __future__ import annotations

from typing import Any

import requests

from config import get_api_base_url


def _build_url(path: str) -> str:
    base = get_api_base_url().strip().rstrip("/")
    if not base:
        raise RuntimeError("API_BASE_URL is not configured.")
    return f"{base}/{path.lstrip('/')}"


def request_json(
    method: str,
    path: str,
    *,
    access_token: str | None = None,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
    timeout: int = 60,
):
    headers = {"Accept": "application/json"}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    response = requests.request(
        method=method.upper(),
        url=_build_url(path),
        headers=headers,
        params=params,
        json=json_body,
        timeout=timeout,
    )

    try:
        payload = response.json()
    except ValueError:
        payload = response.text

    if response.ok:
        return payload

    if isinstance(payload, dict):
        detail = payload.get("detail") or payload.get("message") or str(payload)
    else:
        detail = str(payload)
    raise RuntimeError(f"{response.status_code}: {detail}")
