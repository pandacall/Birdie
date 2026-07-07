## Parent

#1

## What to build

Harden the pipeline to the **failure-handling floor**. **Meta token**: proactive refresh before expiry; on a `401` at publish, **park** the compilation as "blocked — needs re-auth" and notify, never drop. **OBS**: on websocket disconnect mid-game, **salvage** the partial recording and process whatever footage exists; no mid-game relaunch. **Agent crash**: on restart, detect an **orphaned** recording + event log for a finished game and run its post-game pipeline. Post-game is **idempotent, keyed by game id**, so re-runs cannot double-post. Any post-game step failure **parks** the compilation with an error rather than crashing the agent.

## Acceptance criteria

- [ ] Token refreshes proactively; a `401` parks the compilation with a clear reason rather than dropping it
- [ ] An OBS disconnect mid-game yields a compilation from the salvaged partial recording
- [ ] A crash-and-restart recovers an orphaned finished game and processes it
- [ ] Post-game processing is idempotent per game id; a re-run does not double-post
- [ ] A failing post-game step parks the compilation with an error and the agent keeps running

## Blocked by

- #4 (adapters + post-game exist); can run in parallel with #6
