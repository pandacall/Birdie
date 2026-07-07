from pathlib import Path

from birdie.queue import QueuedCompilation
from birdie.webreview import render_page


def _item(id_: str, caption: str) -> QueuedCompilation:
    return QueuedCompilation(id=id_, video=Path(f"{id_}.mp4"), caption=caption, status="pending")


def test_render_page_shows_each_item_with_preview_and_actions() -> None:
    html = render_page([_item("katarina", "Pentakill! <gg>")])

    assert "/video/katarina" in html          # inline preview source
    assert "Pentakill! &lt;gg&gt;" in html     # caption, HTML-escaped
    assert 'value="approve"' in html
    assert 'value="discard"' in html


def test_render_page_handles_empty_queue() -> None:
    html = render_page([])
    assert "No pending" in html
