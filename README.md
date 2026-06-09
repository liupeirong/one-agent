# one-agent

one-agent is being designed as a Python console app for single-shot AI agent
runs. The planned v1 behavior is to load only the Claude-style skills and MCP
servers explicitly mentioned in the prompt, use an OpenAI-compatible LLM API,
and return one final non-streaming answer.

## User Guide

1. Install dependencies:

```cmd
uv sync
```

2. Configure your OpenAI-compatible model with environment variables or a `.env` file:

```txt
OPENAI_API_KEY=...
OPENAI_BASE_URL=...
OPENAI_MODEL=...
```

3. Add optional skills in Claude-style folders:

```txt
~/.claude/skills/<skill-name>/SKILL.md
```

4. Add optional MCP servers in `~/.claude.json`:

```json
{
  "mcpServers": {
    "tavily": {
      "command": "npx",
      "args": ["-y", "tavily-mcp"],
      "env": {
        "TAVILY_API_KEY": "..."
      }
    }
  }
}
```

5. Run one prompt at a time:

```cmd
uv run python main.py "Use @writer /tavily to research current options and summarize them"
```

`@skill-name` loads `~/.claude/skills/<skill-name>/SKILL.md`. `/mcp-name`
loads the matching MCP server from `~/.claude.json` and exposes that server's
tools to the agent. Mentions can appear anywhere in the prompt. If no mentions
are present, no skills or MCP tools are loaded.

## Developer Guide

### Finish setting up the repo

```cmd
uv sync
git init
uv run pre-commit install
uv run pre-commit install --hook-type commit-msg
```

### Run tests

```cmd
uv run pytest
```

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
