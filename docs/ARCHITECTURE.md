## Target v1 Architecture

one-agent will be a Python console application for single-shot AI agent runs. It
will use LangChain, LangGraph, and LangSmith SDKs as the agent framework, with
an OpenAI-compatible chat API as the only supported LLM interface.

The app will not provide multi-turn chat or streaming output. Each invocation
will accept one prompt, may perform internal multi-step reasoning and tool
calls, and will print one final answer.

## User Configuration

### LLM

Model configuration is loaded from environment variables or a project `.env`
file:

```txt
OPENAI_API_KEY=...
OPENAI_BASE_URL=...
OPENAI_MODEL=...
```

The app fails fast when required model configuration is missing.

### Skills

Skills use Claude-style folders under the user's home directory:

```txt
~/.claude/skills/
  writer/
    SKILL.md
  researcher/
    SKILL.md
```

A skill is selected with `@skill-name` anywhere in the user prompt. The skill
name must exactly match the folder name. For v1, only `SKILL.md` is loaded;
sibling files and scripts are not loaded or registered as tools.

Multiple selected skills are loaded in mention order and added to the agent
context with clear boundaries.

### MCP Servers

MCP servers are loaded from `~/.claude.json` using a top-level `mcpServers`
object:

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

An MCP server is selected with `/mcp-name` anywhere in the user prompt. The
mention maps to a server name, not an individual tool name. For v1, only
command-based stdio MCP servers are supported. When a server is selected, all
tools exposed by that server are made available to the agent, and the agent
decides which tools to call. v1 does not provide reusable MCP daemon lifecycle
management; implementations should follow the MCP client library lifecycle and
avoid orphaned child processes.

## Prompt Routing

The prompt parser scans the full prompt for explicit routing mentions:

- `@skill-name` selects a skill.
- `/mcp-name` selects an MCP server.
- Names may contain letters, numbers, `_`, and `-`.
- Mentions are ignored when embedded in another string, such as
  `user@example.com`.
- MCP mentions are ignored for path-like strings with multiple `/` separators.

If no mentions are present, no skills and no MCP servers are loaded. Unknown
skills or MCP servers fail fast with a clear error. Routing mentions are
stripped before the remaining task text is sent to the model. If the remaining
task is empty, the app fails fast.

## Data Flow

```txt
User prompt
  -> parse @skill and /mcp mentions
  -> validate selected skill folders and MCP server configs
  -> strip routing mentions from task text
  -> load selected SKILL.md files as instruction context
  -> start/connect selected MCP stdio servers
  -> expose selected MCP server tools to the LangGraph agent
  -> run one non-streaming agent invocation
  -> print final answer to stdout
```

Errors are printed to stderr and return a nonzero exit code.

## Repo Layout

Target layout as features are implemented:

```txt
main.py                  # Console entry point
src/one_agent/
  __init__.py
  cli.py                 # Argument parsing and process exit behavior
  config.py              # .env and environment configuration
  mentions.py            # @skill and /mcp parsing
  skills.py              # Claude-style SKILL.md loading
  mcp_config.py          # ~/.claude.json parsing and validation
  runtime.py             # LangChain/LangGraph agent assembly and execution

tests/
  test_mentions.py
  test_skills.py
  test_mcp_config.py
```

## Testing Strategy

Prioritize unit tests for:

- mention parsing and stripping behavior,
- skill folder and `SKILL.md` loading,
- `~/.claude.json` MCP server config parsing.

Add basic tests for required LLM environment configuration, but do not overbuild
env handling tests. MCP server integration can be covered with lightweight
fakes or mocks before adding live-server tests.

## Observability

LangSmith tracing is optional. Tracing is enabled only when a LangSmith API key
is configured through the conventional LangSmith environment variables. The app
must run without LangSmith configuration.

## Security

Use Entra ID instead of API key for LLM endpoint authentication.

Users cannot register tools dynamically through the prompt. Tools are exposed
only from MCP servers already configured in `~/.claude.json`, and only when the
server is explicitly mentioned. Skills provide instructions only and do not
register executable tools in v1.

MCP server startup or connection failure fails the run because the user
explicitly requested that server.
