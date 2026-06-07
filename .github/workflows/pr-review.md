---
name: Agentic PR Review
on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]
permissions:
  contents: read
  pull-requests: read
engine:
  id: copilot
  model: claude-opus-4.6
  agent: pr-review
safe-outputs:
  create-pull-request-review-comment:
    max: 10
    side: "RIGHT"
  add-comment:
    hide-older-comments: true
  add-labels:
    max: 3
  remove-labels:
    max: 3
---

# Automated PR Review

The `pr-review` agent provides the review process, dimensions, and
language-specific guidelines. This workflow adds CI-specific adaptations
and output instructions.

## Pre-Review Checks

Before reviewing:

1. **Skip draft PRs** — if the PR is a draft, post a single comment: "⏸️ Skipping review — PR is in draft state. Will review when marked ready." Then stop.
2. **Ignore generated files** — skip `*.lock.yml`, `uv.lock`, and any files under `node_modules/` or `dist/`.
3. **Check existing review comments** — read existing review threads to avoid duplicating previously raised findings.

## Output Instructions

### Step 1 — Clean up stale labels

Remove any existing review outcome labels before adding a new one:

- Remove `review:approved`, `review:needs-changes`, `review:critical` (if present)

### Step 2 — Post inline comments

Use `create-pull-request-review-comment` for issues found on specific lines. Each comment should:

- Name the review dimension (e.g., **Security**, **Correctness**)
- Clearly describe the issue
- Suggest a fix when possible

Focus on **HIGH-SIGNAL findings only**. Do not comment on:

- Style issues that Ruff or Pyright already catch automatically
- Issues already raised in existing review threads on this PR

### Step 3 — Post summary comment

Use `add-comment` to post a summary:

- Overall assessment: ✅ **Looks Good** / ⚠️ **Needs Changes** / 🛑 **Critical Issues**
- Counts of findings by dimension
- Cross-cutting observations (missing tests, documentation gaps, etc.)

### Step 4 — Label the PR

Add exactly one outcome label:

- `review:approved` — no issues or only minor suggestions
- `review:needs-changes` — issues that should be addressed before merge
- `review:critical` — security vulnerabilities, data loss risks, or breaking changes
