"""Meta Graph API publisher adapter (implements the Publisher port).

Publishes a 16:9 regular video post to a Facebook Page we own via
``POST /{page-id}/videos`` using a stored Page access token (ADR 0003 — no
browser automation). Token refresh and 401->park handling arrive in issue #7.
"""

from __future__ import annotations

from pathlib import Path

import requests

_GRAPH = "https://graph.facebook.com"


class MetaPublisher:
    def __init__(
        self,
        page_id: str,
        access_token: str,
        api_version: str = "v21.0",
        timeout: float = 120.0,
    ) -> None:
        self._page_id = page_id
        self._token = access_token
        self._api_version = api_version
        self._timeout = timeout

    def publish(self, video: Path, caption: str) -> str:
        url = f"{_GRAPH}/{self._api_version}/{self._page_id}/videos"
        with video.open("rb") as fh:
            resp = requests.post(
                url,
                data={"description": caption, "access_token": self._token},
                files={"source": fh},
                timeout=self._timeout,
            )
        resp.raise_for_status()
        video_id = resp.json()["id"]
        return str(video_id)
