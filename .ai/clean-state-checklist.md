# Clean State Checklist

Run this checklist before committing and at the end of each session.

## Build

- [ ] `ruff format .` completes successfully
- [ ] `ruff check .` passes with no type error
- [ ] `pytest` passes with no type error

## Runtime

- [ ] Application starts without errors (`python main.py`)
- [ ] Structured log output appears in console at startup

## Repository

- [ ] No unintended files in git status
- [ ] No sensitive data (.env, credentials) staged
- [ ] Verify no referenced files in `CLAUDE.md` or `docs/ARCHITECTURE.md` have been renamed or deleted
