"""Meta Page access token lifecycle: proactive refresh before expiry.

The decision logic (needs_refresh, maybe_refresh) is pure and tested; the actual
Graph API exchange is I/O (manual smoke). Tokens are persisted so a restart
knows when the next refresh is due (ADR 0003 flagged this ~60-day chore).
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import requests

Exchange = Callable[[str], tuple[str, float]]


def needs_refresh(expires_at: float, now: float, threshold_seconds: float) -> bool:
    return (expires_at - now) <= threshold_seconds


class TokenStore:
    def __init__(self, path: Path) -> None:
        self._path = path

    def load(self) -> tuple[str, float] | None:
        if not self._path.exists():
            return None
        data = json.loads(self._path.read_text("utf-8"))
        return str(data["token"]), float(data["expires_at"])

    def save(self, token: str, expires_at: float) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps({"token": token, "expires_at": expires_at}), encoding="utf-8"
        )


def maybe_refresh(
    store: TokenStore,
    now: float,
    threshold_seconds: float,
    exchange: Exchange,
) -> str:
    """Return a healthy token, refreshing (and persisting) it if it's within
    ``threshold_seconds`` of expiry."""
    loaded = store.load()
    if loaded is None:
        raise ValueError("no stored token to refresh")
    token, expires_at = loaded
    if needs_refresh(expires_at, now, threshold_seconds):
        token, expires_at = exchange(token)
        store.save(token, expires_at)
    return token


def refresh_long_lived_token(
    app_id: str,
    app_secret: str,
    token: str,
    api_version: str = "v21.0",
) -> tuple[str, float]:
    """Exchange a token for a fresh long-lived one via the Graph API (I/O)."""
    resp = requests.get(
        f"https://graph.facebook.com/{api_version}/oauth/access_token",
        params={
            "grant_type": "fb_exchange_token",
            "client_id": app_id,
            "client_secret": app_secret,
            "fb_exchange_token": token,
        },
        timeout=30.0,
    )
    resp.raise_for_status()
    data: Any = resp.json()
    expires_in = float(data.get("expires_in", 60 * 24 * 3600))
    return str(data["access_token"]), time.time() + expires_in
