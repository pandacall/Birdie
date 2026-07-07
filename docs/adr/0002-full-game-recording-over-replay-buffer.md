# Full-game recording, not OBS replay buffer

## Status

accepted

Supersedes the "replay buffer" phrasing in the ideation doc's capture decision.

## Context

The ideation doc was internally inconsistent: its "Decisions So Far" chose OBS with the
**replay buffer** (a rolling ring buffer; each trigger saves the last ~N seconds live),
while its MVP scope said OBS **records the full game** and FFmpeg cuts post-game. These are
different architectures. Our product is a per-game **Compilation**: multiple Clips spanning
the whole game, formed by merging Moment clusters and selected by score *after* the game.

## Decision

OBS records the **entire game to a single file** (NVENC). The during-game job only records
and logs Moments with game timestamps; **all cutting, merging, scoring, selection, and
stitching happen post-game**. The replay-buffer approach is rejected.

## Considered Options

- **Replay buffer:** fits a single-clip-on-demand product. Rejected — live trigger timing is
  fragile, buffer length caps clip length, and merging overlapping saves for teamfights is
  awkward. None of it suits post-game scoring/selection over the whole game.
- **Full-game recording (chosen):** merging and scoring become simple arithmetic on
  timestamps; no live-timing fragility.

## Consequences

- Costs disk: a ~40-minute NVENC capture is a few GB (cheap, transient — deleted after the
  Compilation is produced).
- Requires a **timeline-sync anchor** mapping Riot game-time to the recording clock so
  Windows cut at the right frames. (Resolved separately.)
