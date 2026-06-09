# CLAUDE.md

You are working in a repository designed for one-session-per-feature implementation work.
Prioritize reliable completion, continuity across sessions, and explicit
verification over speed.

## Before You Begin Implementing Features

1. Run `pwd` and confirm you are in the expected repository root.
2. Read `.ai/claude-progress.md`.
3. Read `.ai/feature-list.md`.
4. Review recent commits with `git log --oneline -5`.
5. Install or sync dependencies with `uv sync`.
6. Check if tests are already broken with `pytest`.

Then select exactly the highest priority unfinished feature and
work only on that feature until you either verify it or document
why it is blocked.

## Rules

- One active feature at a time.
- Create a new branch if you are on the main branch and starting to implement a new feature.
- Do not claim completion without runnable evidence.
- Do not rewrite the feature list to hide unfinished work.
- Do not remove or weaken tests just to make the task look complete.
- Use repository artifacts as the system of record.
- Stage all changes, but do not commit or push changes.

## Completion Gate

A feature can move to `passing` only after the required verification succeeds
and the result is recorded in the `evidence` field of `.ai/feature-list.md`.

## Before You Stop

1. Run the PR Review agent defined in `.github/agents/pr-review.agent.md` to review all code changes made this session, and address any issues it raises before proceeding.
2. Update progress log in `.ai/claude-progress.md` by recording:
    - current feature state,
    - new decisions made,
    - what is verified, unverified, or broken
    - any unresolved risk
3. Update `README.md` if anything changed that affects end-user or developer experience.
4. Check `.ai/clean-state-checklist.md` to leave the repo in a clean state for the next session.
