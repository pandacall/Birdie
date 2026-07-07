"""Local review web page (thin adapter over ReviewService).

``render_page`` is pure and covered by tests; the HTTP server is manual-smoke
I/O. Serves each pending compilation with an inline video preview, an editable
caption, and Approve/Discard actions.
"""

from __future__ import annotations

from functools import partial
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from birdie.queue import QueuedCompilation
from birdie.review import ReviewService


def render_page(items: list[QueuedCompilation]) -> str:
    if not items:
        body = "<p>No pending compilations.</p>"
    else:
        body = "\n".join(_render_item(item) for item in items)
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>Birdie Review</title></head><body>"
        "<h1>Review queue</h1>" + body + "</body></html>"
    )


def _render_item(item: QueuedCompilation) -> str:
    return (
        '<div class="item" style="margin-bottom:2rem">'
        f'<video src="/video/{escape(item.id)}" controls width="480"></video>'
        '<form method="post" action="/action">'
        f'<input type="hidden" name="id" value="{escape(item.id)}">'
        '<div><textarea name="caption" rows="4" cols="60">'
        f"{escape(item.caption)}</textarea></div>"
        '<button name="action" value="approve">Approve &amp; Post</button> '
        '<button name="action" value="discard">Discard</button>'
        "</form></div>"
    )


class _Handler(BaseHTTPRequestHandler):
    def __init__(self, *args: object, service: ReviewService, **kwargs: object) -> None:
        self._service = service
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            self._send_html(render_page(self._service.pending()))
        elif path.startswith("/video/"):
            self._send_video(path.removeprefix("/video/"))
        else:
            self.send_error(404)

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/action":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", 0))
        form = parse_qs(self.rfile.read(length).decode("utf-8"))
        item_id = form.get("id", [""])[0]
        action = form.get("action", [""])[0]
        caption = form.get("caption", [""])[0]

        if action == "approve":
            self._service.edit(item_id, caption)
            self._service.approve(item_id)
        elif action == "discard":
            self._service.discard(item_id)

        self.send_response(303)
        self.send_header("Location", "/")
        self.end_headers()

    def _send_html(self, html: str) -> None:
        payload = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_video(self, item_id: str) -> None:
        try:
            item = self._service.get(item_id)
        except KeyError:
            self.send_error(404)
            return
        data = item.video.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "video/mp4")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args: object) -> None:  # quieter console
        pass


def serve(service: ReviewService, host: str = "127.0.0.1", port: int = 8765) -> None:
    handler = partial(_Handler, service=service)
    server = ThreadingHTTPServer((host, port), handler)
    print(f"Review queue at http://{host}:{port}  (Ctrl-C to stop)")
    server.serve_forever()
