# PRD: LoL Highlights → Facebook Auto-Post Pipeline (MVP)

Status: ready-for-agent

> Domain vocabulary in this PRD (event, moment, window, clip, compilation, category,
> output profile, agent, timeline anchor, posting mode, rule, gate, review queue, caption,
> tone) is defined in `CONTEXT.md`. Architectural decisions referenced are in `docs/adr/`.

## Problem Statement

I play League of Legends and want a consistent stream of shareable content on a Facebook
Page I own, without manually recording, editing, captioning, and posting after every game.
Doing this by hand is tedious enough that it doesn't happen, so good (and funny-bad) moments
never make it out. I want *every* game — a stomp, a coinflip, or a game where I inted — to
turn into a watchable post, because even a bad game is content when it's framed as a blooper.

## Solution

A local pipeline (the **agent**) runs on my gaming PC. While I play, it records the full
game via OBS and logs the game's **events** from the Riot Live Client Data API. When the
game ends, it scores those events into **moments**, merges nearby moments into **windows**,
cuts each window into a **clip**, selects the best clips into one per-game **compilation**,
writes a template-based **caption**, and routes the compilation through a **gate**: trusted
cases auto-publish to the Facebook Page via the Meta Graph API; everything else lands in a
local **review queue** web page where I approve, edit the caption, or discard. Every game
yields exactly one compilation — the scorer *selects* content, it never gates a game out.

## User Stories

1. As a player, I want the agent to detect when a game starts automatically, so that I never
   have to remember to start recording.
2. As a player, I want OBS to record the entire game to a single file, so that no moment is
   ever lost to a mistimed capture trigger.
3. As a player, I want the agent to capture a timeline anchor at recording start, so that
   game-time event timestamps map correctly to positions in the recording.
4. As a player, I want the agent to read the Riot Live Client Data API event stream during
   the game, so that highlight-worthy occurrences are detected without screen analysis.
5. As a player, I want each event filtered to my own participant, so that other players'
   kills and deaths don't get attributed to me.
6. As a player, I want the agent to detect when the game ends, so that post-game processing
   starts on its own.
7. As a player, I want every game to produce exactly one compilation, so that I always have
   something to post — even from a bad game.
8. As a player, I want events scored into moments post-game, so that scoring is deterministic
   and can be re-tuned against saved logs.
9. As a player, I want nearby moments merged into a single window, so that one teamfight
   becomes one clip instead of several fragments.
10. As a player, I want a clip's score aggregated from its moments, so that a big teamfight
    ranks above a lone kill.
11. As a player, I want each clip tagged with a category (epic or blooper), so that captions
    and framing match whether the moment was impressive or funny-bad.
12. As a player, I want a death to route a clip to the blooper category rather than being
    discarded, so that my dumb deaths become content instead of disappearing.
13. As a player, I want clips ranked and selected up to a length budget, so that a long game
    doesn't produce an unwatchably long compilation.
14. As a player, I want the selected clips assembled in chronological order, so that the
    compilation tells the game's story in sequence.
15. As a player, I want a one-clip game to still produce a compilation, so that the
    per-game guarantee always holds.
16. As a player, I want at least one blooper included when one exists and none made the
    budget, so that even my best games keep a self-deprecating moment.
17. As a player, I want a template caption built from match data (champion, KDA, result,
    standout events), so that the post always states correct facts.
18. As a player, I want caption tone to shift with the compilation's dominant category, so
    that epic games read hype and blooper games read self-deprecating.
19. As a player, I want a core set of hashtags derived from match data, so that posts are
    discoverable without me writing tags every time.
20. As a player, I want the gate to evaluate rules top-to-bottom with first-match-wins, so
    that I can express "pentakills auto-post, everything else review."
21. As a player, I want the default posting mode to be review, so that nothing embarrassing
    goes out without my okay unless I explicitly trust it.
22. As a player, I want a rule to auto-publish trusted compilations (e.g. contains a
    pentakill), so that clearly-great content ships without waiting on me.
23. As a player, I want a local web page listing pending compilations with an inline video
    preview and the caption, so that I can review on my PC.
24. As a player, I want to approve a compilation from the review queue, so that it publishes
    as-is.
25. As a player, I want to edit a caption before approving, so that I can tweak the wording.
26. As a player, I want to discard a compilation, so that content I don't like never posts.
27. As a player, I want approved and auto-eligible compilations published to my Facebook Page
    via the Meta Graph API, so that posting is hands-off and keeps my Page safe (ADR 0003).
28. As a player, I want the agent to publish 16:9 regular video posts, so that the full game
    is visible without lossy cropping (ADR 0001).
29. As a player, I want the Meta access token refreshed proactively before expiry, so that
    publishing doesn't silently break every ~60 days.
30. As a player, I want a compilation that fails to publish (e.g. expired token) parked in
    the review queue with a clear reason, so that it's never silently lost.
31. As a player, I want the agent to salvage a partial recording if OBS disconnects
    mid-game, so that a crash costs me at most the tail of a game, not the whole thing.
32. As a player, I want the agent to recover an orphaned recording and moment log after a
    crash on restart, so that a completed game still gets processed.
33. As a player, I want post-game processing to be idempotent per game, so that a re-run
    can never double-post.
34. As a player, I want a post-game step failure (FFmpeg/publish) to park the compilation
    with an error rather than crash the agent, so that one bad game doesn't stop the pipeline.
35. As a player, I want all tuning values (merge gap, length budget, event scores, rules,
    default tone) in a config file, so that I can adjust behavior without changing code.
36. As a developer, I want the transient full-game recording deleted once its compilation is
    produced, so that disk usage stays bounded.
37. As a developer, I want the post-game decision logic isolated as a pure planner function,
    so that scoring, selection, gating, and captioning are testable without OBS, FFmpeg, or
    the network.
38. As a developer, I want the publish format modeled as a swappable output profile, so that
    a future 9:16 Reel profile can be added without reworking the pipeline (ADR 0001).
39. As a developer, I want a walking-skeleton milestone that proves OBS control, Meta
    publish, and FFmpeg cut/stitch end-to-end, so that the riskiest integrations are
    validated before building the scoring and selection logic.

## Implementation Decisions

**Language & shape.** Python, single repo (`Birdie`), one module per pipeline stage
(recorder, game-watcher, planner, editor, captioner, gate, publisher, review-queue/web) plus
a single TOML config. The **agent** is one long-running process with two phases; state is
files on disk, not services (single-user desktop tool).

**During-game phase.** Triggered when `:2999` starts responding. Drives OBS to start
recording (obs-websocket, assume OBS already running with a preconfigured scene). Captures
the **timeline anchor** — one `(recording position, game clock)` pair. Appends **raw events**
(with game timestamps) filtered to the active player into a per-game event log. Detects game
end when `:2999` stops responding, then stops recording and hands off.

**Post-game phase — the planner (pure).** `plan_compilation(event_log, match_data, config)
→ CompilationPlan`. Runs: score events into **moments**; **merge pass** groups moments whose
windows fall within `merge_gap` into **windows**; each window's clip gets an aggregate score
(diminishing-returns sum of its moments) and a **category** (`epic`/`blooper`, deaths route
to blooper); **selection** ranks clips by score, fills to the **length budget** (~75s),
guarantees ≥1 clip, and reserves a slot for the top blooper if one exists and none made the
budget; clips are ordered chronologically; the **gate** evaluates the ordered **rule** list
(first-match-wins, default `review`) against compilation-level signals (contained event
types, peak clip category, aggregate score) to pick a **posting mode**; a template
**caption** is produced with tone shifted by dominant category. The `CompilationPlan` is the
ordered list of windows to cut + caption + posting mode.

**Editing.** A `VideoEditor` executes a `CompilationPlan` with FFmpeg: cut windows from the
recording (stream-copy), concat, render the `video` output profile (16:9, no length cap).

**Publishing.** `Publisher` posts 16:9 regular video posts via the Meta Graph API
(`POST /{page-id}/videos`) to a Page we own, using a stored long-lived Page access token with
proactive refresh; on `401`, park the compilation. Browser automation is rejected (ADR 0003).

**Gating & review.** Default posting mode is `review`. `auto` compilations publish directly;
`review` compilations enter the durable **review queue** backing a local web page with
approve / edit-caption / discard. Video re-editing in the queue is out of scope.

**Failure handling.** Never lose footage (full recording + orphan recovery), never silently
drop a compilation (park on failure), degrade instead of crash (salvage partial recordings;
missed events cost only scoring accuracy). Post-game is idempotent, keyed by game id.

**Config (TOML tuning knobs).** `merge_gap` (~6s), length budget (~75s), per-event `scores`
+ aggregate formula, ordered `rules` (default `review`), default `tone`.

**Milestones (build order, not calendar).**
- **M0 — walking skeleton:** manual trigger; record one game; cut one hardcoded window;
  template caption; publish to a test Page. Validates obs-websocket, Meta token+publish, and
  FFmpeg cut/stitch — the integrations most likely to sink the project.
- **M1 — designed MVP:** auto game detection, the pure planner (score→merge→select→gate→
  caption), the local review web page, publish-on-approve, failure handling floor.

## Testing Decisions

**What makes a good test here:** assert external behavior (a plan's chosen windows, order,
caption text, posting mode; a store's state transitions), never internal wiring. The planner
is a pure function, so its tests are input→output with no mocks.

**Primary seam — the planner** (`plan_compilation`): the single high seam carrying nearly all
decision logic. Tested exhaustively with **fixture event logs** (real games captured as JSON
and replayed): merge behavior across `merge_gap` boundaries, clip aggregate scoring, category
tagging (death→blooper), selection under the length budget, the one-clip guarantee, the
reserved-blooper-slot swap, rule evaluation (first-match-wins, default `review`), and caption
text/tone by dominant category.

**Secondary seams — thin adapters, faked:**
- **GameWatcher** (Riot :2999): tests replay recorded event-log fixtures; assert
  game-start/end detection and correct active-player filtering.
- **Recorder** (obs-websocket): faked; assert start/stop and anchor capture.
- **VideoEditor** (FFmpeg): assert it's invoked with the plan's exact window list and output
  profile; actual encode correctness is a manual smoke test, not a unit test.
- **Publisher** (Meta Graph API): faked HTTP; contract tests for the publish call, the
  token-refresh flow, and the `401`→park path.
- **ReviewQueue**: test enqueue / approve / park / discard against the store interface, not
  the web page.

**Prior art:** none — greenfield. Use pytest, fixture-replay for event logs, and fake
adapters defined via `typing.Protocol` boundaries.

## Out of Scope

- **9:16 Reels** and any smart per-clip cropping (deferred; format is a swappable output
  profile — ADR 0001).
- **LLM captions** — MVP is template-only; the local open-source LLM (Ollama) flavor layer is
  iteration 2.
- **Auto-post rules beyond simple trusted carve-outs** — M1 routes essentially everything to
  review; richer auto rules come later.
- **Telegram / chat-bot review** — MVP is the local web page only; a phone notifier is a
  later add-on.
- **On-screen overlays, stat cards, intro/outro, background music** — editing polish, later.
- **Weekly / session "best-of" roll-up compilations** — per-game only for MVP.
- **Vision/audio highlight fallback** — full recording makes missed events low-cost; skip.
- **Mid-game OBS auto-relaunch** and sophisticated retry/backoff — salvage-partial and
  retry-then-park suffice for one user.
- **Video re-editing inside the review queue** — approve / edit-caption / discard only.
- **Auto-launching/configuring OBS** — assume OBS is already running.

## Further Notes

- **User-only prerequisite:** create a Meta developer app (dev mode — no App Review for your
  own Page), grant `pages_manage_posts` + `pages_show_list` + `pages_read_engagement`, and
  obtain a long-lived Page access token. This is free (ADR 0003) but manual and is the
  riskiest integration — do it during M0. Verify the current permission/verification
  requirements at build time, as Meta reshuffles them.
- **Riot ToS:** the Live Client Data API is official and read-only — fine. Re-check Riot's
  developer policies before publishing the project publicly.
- **CONTEXT.md refinement adopted during PRD:** the during-game log stores raw events;
  scoring moved fully into the post-game planner, strengthening the "capture everything,
  decide later" selector philosophy and keeping scoring re-tunable against saved logs.
