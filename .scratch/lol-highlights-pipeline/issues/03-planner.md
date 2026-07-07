## Parent

#1

## What to build

Implement the pure planner `plan_compilation(event_log, match_data, config) -> CompilationPlan`. Score raw events into **moments**; run the **merge pass** grouping moments within `merge_gap` into **windows**; compute each **clip**'s aggregate score (diminishing-returns sum) and **category** (`epic`/`blooper`, deaths route to blooper); **select** clips ranked by score up to the **length budget** with the one-clip guarantee floor and the reserved-blooper-slot swap; order selected clips chronologically. The VideoEditor cuts all selected windows (stream-copy) and concatenates them into a single **compilation**, replacing the skeleton's naive single clip.

## Acceptance criteria

- [ ] A real game produces a multi-clip compilation assembled from the event log
- [ ] Adjacent moments within `merge_gap` collapse into one window/clip
- [ ] Clip scores aggregate from constituent moments; clips carry an epic/blooper category; deaths route to blooper
- [ ] Selection fills to the length budget, always yields >=1 clip, and includes a blooper when one exists but none made the budget
- [ ] Selected clips are stitched in chronological order
- [ ] The planner is a pure function tested with fixture event logs (no OBS/FFmpeg/network)

## Blocked by

- #3
