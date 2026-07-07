#!/usr/bin/env bash
# Publish the LoL-highlights PRD to GitHub Issues.
# Prereqs (one time): a fresh shell so `gh` is on PATH, then `gh auth login`.
set -euo pipefail

PRD="$(cd "$(dirname "$0")" && pwd)/PRD.md"
TITLE="PRD: LoL Highlights → Facebook Auto-Post Pipeline (MVP)"
REPO="pandacall/Birdie"

command -v gh >/dev/null || { echo "gh not on PATH — open a NEW terminal (winget installed it) or install from https://cli.github.com"; exit 1; }
gh auth status >/dev/null 2>&1 || { echo "Not authenticated — run: gh auth login"; exit 1; }

# Create the five canonical triage labels (ignore if they already exist).
gh label create needs-triage     --repo "$REPO" --color "d4c5f9" --description "Maintainer needs to evaluate" 2>/dev/null || true
gh label create needs-info       --repo "$REPO" --color "fef2c0" --description "Waiting on reporter" 2>/dev/null || true
gh label create ready-for-agent  --repo "$REPO" --color "0e8a16" --description "Fully specified, AFK-ready" 2>/dev/null || true
gh label create ready-for-human  --repo "$REPO" --color "1d76db" --description "Needs human implementation" 2>/dev/null || true
gh label create wontfix          --repo "$REPO" --color "e6e6e6" --description "Will not be actioned" 2>/dev/null || true

# Create the issue from the PRD, tagged ready-for-agent.
gh issue create --repo "$REPO" --title "$TITLE" --body-file "$PRD" --label ready-for-agent
