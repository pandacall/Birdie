"""Riot Live Client Data API adapter (implements the LiveClient port).

Reads localhost:2999 over HTTPS with a self-signed cert (verify disabled). When
no game is running the endpoint refuses the connection; ``active_player``
returns None in that case, which the watcher treats as "no game / game over".
"""

from __future__ import annotations

from typing import Any

import requests
import urllib3

_BASE = "https://127.0.0.1:2999/liveclientdata"

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class RiotLiveClient:
    def __init__(self, base_url: str = _BASE, timeout: float = 2.0) -> None:
        self._base = base_url
        self._timeout = timeout
        self._session = requests.Session()
        self._session.verify = False

    def active_player(self) -> str | None:
        try:
            resp = self._session.get(
                f"{self._base}/activeplayername", timeout=self._timeout
            )
            resp.raise_for_status()
        except requests.RequestException:
            return None
        return str(resp.json())

    def game_time(self) -> float:
        resp = self._session.get(f"{self._base}/gamestats", timeout=self._timeout)
        resp.raise_for_status()
        data: Any = resp.json()
        return float(data.get("gameTime", 0.0))

    def event_dicts(self) -> list[dict[str, Any]]:
        try:
            resp = self._session.get(
                f"{self._base}/eventdata", timeout=self._timeout
            )
            resp.raise_for_status()
        except requests.RequestException:
            return []
        data: Any = resp.json()
        return list(data.get("Events", []))
