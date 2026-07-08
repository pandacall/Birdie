# Birdie

Automated pipeline that captures League of Legends gameplay, detects highlight moments, edits
per-game compilations, generates captions, and publishes them to a Facebook Page.

## Commands

```bash
pip install -e ".[dev]"      # install with dev deps (pytest, mypy)
pytest                       # run the test suite (tests/)
mypy                         # strict type check (configured in pyproject.toml)

birdie skeleton --champion Ahri --kills 5 --deaths 2 --assists 8 --result Victory
birdie watch                 # auto-detect games, record, post-process
birdie review                # serve the local review-queue web page (127.0.0.1:8765)
```

Copy `birdie.example.toml` to `birdie.toml` (git-ignored) before running.

## Architecture

Single long-running process (the **Agent**), files on disk as state — no services/DB.
Ports-and-adapters: `birdie/ports.py` defines `Protocol` seams (LiveClient, Recorder,
VideoEditor, Captioner, Publisher); `birdie/adapters/` wraps the real externals (OBS,
FFmpeg, Riot Live Client, Meta Graph API); tests substitute fakes (`tests/fakes.py`).

Flow: `watcher` detects a game → `ObsRecorder` records + Riot events logged →
post-game (`postgame.py`) runs `signals`/`scoring`/`planner` → `gate` decides
auto-publish vs. review → `MetaPublisher` posts or `queue` holds it. `run_post_game`
is idempotent (a `ledger` prevents double-posts) and crash-safe (failures **park** in
the queue, never drop; `recover_orphans` reprocesses games left by a crash).

Entry point: `birdie/cli.py` (`birdie` console script). Domain vocabulary and
rationale live in `CONTEXT.md` + `docs/adr/` (see Domain docs below).

## Environment

Secrets come from env vars, **never** the config file:
- `BIRDIE_OBS_PASSWORD` — obs-websocket password
- `BIRDIE_META_TOKEN` — Meta Page access token (required)
- `BIRDIE_META_APP_ID` / `BIRDIE_META_APP_SECRET` — optional; enable token auto-refresh

## Agent skills

### Issue tracker

Issues and PRDs live as GitHub issues in `pandacall/Birdie` (via the `gh` CLI); external PRs
are not a triage surface. See `docs/agents/issue-tracker.md`.

### Triage labels

Canonical triage roles map to identically-named labels. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `CONTEXT.md` (glossary) + `docs/adr/` (decisions) at the repo root. See
`docs/agents/domain.md`.
