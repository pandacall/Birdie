# LoL Highlights → Facebook Pipeline

Vocabulary for a pipeline that captures League of Legends gameplay, detects highlight
moments, edits clips, generates captions, and publishes them to a Facebook Page.

## Language

### Detection

**Event**:
A single raw occurrence read from the Riot Live Client Data API (e.g. `ChampionKill`,
`Multikill`, `DragonKill`), with a game timestamp. The unedited input signal.
_Avoid_: kill, trigger.

**Moment**:
One scored Event — an Event plus the score the scorer assigned it. The atomic unit of
"something happened worth noticing."
_Avoid_: highlight (a highlight is the merged result, not a single moment), play.

**Window**:
A time span `[start, end]` on the recording timeline that will be physically cut from the
footage. Derived from one or more Moments after a merge pass.
_Avoid_: segment, span, range.

**Merge pass**:
The post-game step that groups Moments whose Windows fall within `merge_gap` of each other
into a single Window. Adjacent teamfight Moments collapse into one Window.

### Output

**Clip**:
The rendered video of a single play — produced from one merged Window. One Window → one
Clip. Carries an aggregate score derived from its constituent Moments. A Clip is an
*ingredient*, not the final post.
_Avoid_: highlight, video, reel (a Reel is a publish format, not the artifact itself).

**Compilation**:
The final posted artifact — the Clips from one game stitched, in chronological order, into
a single video. Exactly one Compilation per game (the per-game guarantee). A Compilation
mixes categories freely; it is not split into separate highlight/fail videos.
_Avoid_: montage, reel, recap, video.

**Category**:
A per-Clip tag describing the *kind* of moment: `epic` (multikills, clutch plays,
objectives) or `blooper` (deaths, botched plays — funny-bad content). Drives caption tone
and any on-screen label. It does not split the Compilation.
_Avoid_: type, kind, class.

**Output profile**:
The target shape of the published video: aspect ratio + length rules. MVP ships one profile,
`video` (16:9, no length cap). A future `reel` profile (9:16, ≤60s, smart-cropped) is a
committed direction. See ADR 0001.
_Avoid_: format, aspect.

### Captioning

**Caption**:
The text body of the Facebook post, written **per Compilation** (describes the whole game),
not per Clip. Facts (champion, KDA, result, standout events) come deterministically from
match data via a template; an optional LLM layer only adds flavor around those facts — it
never originates facts. MVP is template-only; the LLM flavor layer is iteration 2.
_Avoid_: title, description, text.

**Tone**:
The voice of a Caption: `hype` | `deadpan` | `self-deprecating`. A global default that
auto-shifts toward the Compilation's dominant Category (epic-heavy → `hype`, blooper-heavy →
`self-deprecating`).
_Avoid_: voice, style, mood.

### Runtime

**Agent**:
The single long-running process. During a game it records (drives OBS) and logs Moments; at
game end it runs the post-game pipeline. One process, files on disk as state — not services.
_Avoid_: daemon, service, worker.

**Timeline anchor**:
The single `(recording position, game clock)` pair captured at recording start. Every
Moment's game timestamp maps to a recording offset by arithmetic against this anchor. Bridges
Riot game-time and the OBS recording clock.
_Avoid_: offset, sync point.

### Gating & publishing

**Posting mode**:
How a Compilation reaches the Page: `auto` (published without human action) or `review`
(held for approval). The MVP **default is `review`**; `auto` is carved out only by explicit
Rules for trusted cases.
_Avoid_: mode, auto-post flag.

**Rule**:
A condition on a *finished Compilation* mapped to a Posting mode. Keys on compilation-level
signals — event types it contains (e.g. pentakill), its peak Clip's Category, its aggregate
score. Rules are evaluated top-to-bottom, **first match wins**, with a default (`review`) at
the bottom.
_Avoid_: filter, policy, trigger.

**Gate**:
The step that evaluates the Rules against a finished Compilation and routes it to either
auto-publish or the review queue. The single decision point between production and publishing.
_Avoid_: check, gatekeeper.

**Review queue**:
The durable store of Compilations awaiting a human decision. Backs the local review web page.
Compilations that fail to publish (e.g. expired token) are *parked* here rather than dropped —
nothing is ever silently lost. Supported actions: approve, edit caption, discard.
_Avoid_: inbox, pending list.

## Scoring & selection

The scorer is a **selector, not a gate**: every game always yields one Compilation, even a
bad one. Score *ranks* Clips (to decide inclusion order / trimming to a length budget); it
does not decide whether a game gets posted at all. There is no death-after-kill *penalty* —
a death routes a Clip to the `blooper` Category rather than discarding it.

**Compilation assembly:** rank Clips by score desc → fill up to a **length budget** (~75s
default) highest-first → re-sort the chosen Clips chronologically for the stitch. Guarantee
floor: a 1-Clip game still posts. **Reserved blooper slot:** if no `blooper` Clip made the
budget but one exists, swap the lowest-scored `epic` for the top `blooper`.

## Tuning knobs (config, not architecture)

These live in a TOML config and are tuned by feel, not decided here:

- `merge_gap` — max gap between Moments to merge into one Window (start ~6s).
- Length budget — target Compilation duration (start ~75s).
- `scores` — per-event-type base scores; the Clip aggregate formula.
- `rules` — the ordered Rule list (default `review`).
- Tone default.
