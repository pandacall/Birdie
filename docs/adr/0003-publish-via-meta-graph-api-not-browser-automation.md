# Publish via the Meta Graph API, not browser automation

## Status

accepted

## Context

Publishing to a Facebook Page was reconsidered mid-design: the worry was that Meta's API
might be paywalled or walled behind App Review, which prompted looking at a browser-
automation agent (driving the Facebook web UI) as an alternative.

On inspection the premise was wrong. Posting to a **Page you own** via the Graph API
(`POST /{page-id}/videos`) requires **no App Review** — a developer app in **dev mode** with
`pages_manage_posts` (+ `pages_show_list`, `pages_read_engagement`) is sufficient. The Meta
developer account, the app, the API calls, and long-lived tokens are all **free**. App
Review is only needed to let *other* users' accounts use the app. Business verification may
gate some permissions but is itself free.

## Decision

Publish through the **Meta Graph API to a Page we own**. Browser automation of the Facebook
web UI is rejected.

## Considered Options

- **Browser-automation agent (rejected):** violates Facebook's terms on automated access;
  the realistic downside is the account or Page being flagged/banned — catastrophic, since
  the project's whole goal is to *grow* that Page. Also fragile (UI changes break it) and
  requires storing FB session credentials. Its only unique capability — posting to a
  personal profile — is already a non-goal.
- **Meta Graph API (chosen):** sanctioned, free, keeps the Page safe.

## Consequences

- Page access tokens expire (~60 days); a **token-refresh flow** is required and is handled
  as a first-class failure-handling concern.
- The exact set of permissions behind business verification can change; verify the current
  permission requirements at build time rather than trusting a fixed list.
