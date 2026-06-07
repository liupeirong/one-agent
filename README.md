# one-agent

## Getting Started

### Finish setting up the repo

- run `uv sync`
- run `git init`
- run `uv run pre-commit install`
- run `uv run pre-commit install --hook-type commit-msg`

### Verify the repo is set correctly

- copy `.env.sample` to `.env`
- run `uv run main.py`
- run `uv run pytest`

### Build the feature list with AI

Start a session with AI to brainstorm what to build and key architecture design.
The output should be:

- `.ai/feature-list.md`
- `docs/ARCHITECTURE.md`

### Build features

Start a new AI session to build features one by one.
Once AI is done building the feature, review the code.
Ask the draft-commit agent to draft commit message and commit.
When you publish to github, the pr-review agent will automatically review the code.
