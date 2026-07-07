## Parent

#1

## What to build

A local **web page** (served by the agent) listing pending compilations from the review queue, each with an inline **video preview** and the **caption** in an editable field, plus **Approve / Edit caption / Discard** actions. Approve (optionally after editing the caption) publishes the compilation via the Meta Graph API. No video re-editing.

## Acceptance criteria

- [ ] The page lists all pending compilations with inline video preview and current caption
- [ ] Approve publishes the compilation to the Page
- [ ] Editing the caption then approving publishes with the edited text
- [ ] Discard removes a compilation without publishing
- [ ] Queue store operations (enqueue/approve/park/discard) are tested against the store interface, not the web page

## Blocked by

- #5
