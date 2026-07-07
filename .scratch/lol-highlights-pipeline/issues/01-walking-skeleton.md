## Parent

#1

## What to build

The thinnest complete path through every integration layer, manually triggered. A single CLI command records gameplay via OBS (obs-websocket, assume OBS already running), cuts **one hardcoded window** from the recording with FFmpeg and renders the 16:9 `video` **output profile**, builds a **template caption** from sample match data, and publishes the result to a **test Facebook Page** via the Meta Graph API (`POST /{page-id}/videos`). No game detection, no scoring, no review.

This slice lays the foundation: one module per stage behind `typing.Protocol` adapter seams (Recorder, VideoEditor, Captioner, Publisher), a TOML config, and the `video` output-profile abstraction. Proves the three riskiest integrations early (obs-websocket, FFmpeg, Meta publish).

## Acceptance criteria

- [ ] A single command records via OBS, produces a 16:9 video, and publishes it to a test Page
- [ ] The published post carries a template caption built from provided match data (correct facts)
- [ ] Output is a 16:9 regular video post, not a Reel (ADR 0001)
- [ ] Recorder / VideoEditor / Captioner / Publisher exist behind `Protocol` seams; post-game logic is invoked as a pure planning step (trivial here)
- [ ] Tuning values live in a TOML config file
- [ ] The transient recording is deleted once the post is produced
- [ ] Publishing uses a stored Page access token (ADR 0003); no browser automation

## Blocked by

None - can start immediately
