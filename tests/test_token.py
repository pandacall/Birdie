from pathlib import Path

from birdie.token import TokenStore, maybe_refresh, needs_refresh


def test_needs_refresh_within_threshold() -> None:
    # expires in 3 days, threshold 7 days -> refresh
    assert needs_refresh(expires_at=300.0, now=300.0 - 3 * 86400, threshold_seconds=7 * 86400)
    # expires in 10 days -> no refresh
    assert not needs_refresh(
        expires_at=300.0, now=300.0 - 10 * 86400, threshold_seconds=7 * 86400
    )


def test_token_store_round_trips(tmp_path: Path) -> None:
    store = TokenStore(tmp_path / "token.json")
    assert store.load() is None

    store.save("abc", expires_at=12345.0)

    assert TokenStore(tmp_path / "token.json").load() == ("abc", 12345.0)


def test_maybe_refresh_exchanges_when_near_expiry(tmp_path: Path) -> None:
    store = TokenStore(tmp_path / "token.json")
    store.save("old", expires_at=1000.0)
    exchanged: list[str] = []

    def exchange(token: str) -> tuple[str, float]:
        exchanged.append(token)
        return ("new", 9999.0)

    result = maybe_refresh(store, now=1000.0, threshold_seconds=100.0, exchange=exchange)

    assert result == "new"
    assert exchanged == ["old"]
    assert store.load() == ("new", 9999.0)


def test_maybe_refresh_keeps_token_when_healthy(tmp_path: Path) -> None:
    store = TokenStore(tmp_path / "token.json")
    store.save("healthy", expires_at=1_000_000.0)

    def exchange(token: str) -> tuple[str, float]:
        raise AssertionError("should not refresh a healthy token")

    result = maybe_refresh(store, now=0.0, threshold_seconds=100.0, exchange=exchange)

    assert result == "healthy"
