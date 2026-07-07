# Publish 16:9 regular video posts for MVP; defer 9:16 Reels

## Status

accepted

## Context

The final artifact is a per-game **Compilation** of several Clips. Meta pushes 9:16 Reels
harder in its algorithm, so Reels are the better growth vehicle for a cold-start Page. But
League of Legends is a fullscreen 16:9 game whose information is spread across the entire
screen (minimap bottom-right, HP/ability bars, teamfights spanning the width). A naive
center-crop to 9:16 discards the minimap and half of every fight, and Reels' 4–60s cap
fights the multi-clip Compilation model.

## Decision

The MVP publishes **16:9 regular video posts** (`POST /<PAGE_ID>/videos`), native to the
game: no cropping, no length cap, and cut-and-concat FFmpeg only — which keeps the MVP
weekend-sized. Publish format is modelled as a swappable **output profile**, not a baked-in
assumption, because 9:16 Reels are a committed future direction, not a rejected one.

9:16 Reels are deferred to a later phase and require *smart* per-clip cropping
(follow the champion/action) plus a ≤60s length budget — worth doing only when it can be
done well, since a bad crop would hurt the Page more than the lost reach.

## Consequences

- Up-front cost: we forgo Reel algorithmic reach until the 9:16 profile ships.
- The editing stage must treat aspect ratio / length as parameters of an output profile so
  the 9:16 profile can be added without reworking selection, scoring, or publishing.
