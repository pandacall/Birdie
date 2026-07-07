## Parent

#1

## What to build

A **GameWatcher** that polls the Riot Live Client Data API at `localhost:2999`. When the endpoint starts responding, a game is live: start recording and capture the **timeline anchor** (one `(recording position, game clock)` pair). Poll the event stream, appending **raw events** — filtered to the **active player** — with game timestamps to a per-game **event log**. When the endpoint stops responding, the game has ended: stop recording and trigger the post-game step. Runs as the single long-running **agent** process; state is files on disk.

## Acceptance criteria

- [ ] Starting a game automatically starts OBS recording with no manual trigger
- [ ] A timeline anchor is captured at recording start so event game-times map to recording offsets
- [ ] Raw events are logged with game timestamps, filtered to the active player only
- [ ] Ending a game automatically stops recording and kicks off post-game processing
- [ ] The agent runs as a single long-running process; recording + event log persist on disk

## Blocked by

- #2
