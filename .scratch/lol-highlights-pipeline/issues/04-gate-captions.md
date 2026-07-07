## Parent

#1

## What to build

Add the **gate**: evaluate an ordered **rule** list (first-match-wins, default `review`) against compilation-level signals (contained event types, peak clip category, aggregate score) to assign a **posting mode**. Wire the `auto` path (publish immediately) and persist `review`/parked compilations to a durable **review queue** store. Complete the **captioner**: **tone** shifts with the compilation's dominant category (epic->hype, blooper->self-deprecating) and a template-driven hashtag set derived from match data. Config gains `rules` and default `tone`.

## Acceptance criteria

- [ ] Compilations matching an `auto` rule publish without human action; all others persist to the review queue store
- [ ] The default posting mode is `review`
- [ ] Rules evaluate top-to-bottom, first match wins, keyed on compilation-level signals
- [ ] Captions are template-built facts with tone shifted by dominant category and a capped hashtag set
- [ ] `rules` and `tone` are configurable in the TOML config
- [ ] Gate and captioner are tested via the planner seam with fixtures

## Blocked by

- #4
