# one-agent feature list

> Note: Work with the user to record features in the features field of this TypeScript interface:
enum status_legend {
    not_started, // Work has not begun
    in_progress, // The feature is the current active task
    blocked, // Work cannot continue until a documented blocker is resolved
    passing // Required verification has passed and evidence is recorded
},
interface feature_list {
    last_updated: string, // YYYY-MM-DD HH-mm
    id: string; // ex. "db-integration-001",
    priority: number; // 1, 2, 3 - from high to low
    area: string; // ex. "llm integration", "memory management"
    title: string;
    user_visible_behavior: string; // what can the user do?
    status: status_legend;
    verification: string[]; // what needs to be true to call the feature complete
    evidence: string[]; // what's validated
    notes: string; // anything to note about this feature
}[]

```json
[
  {
    "last_updated": "2026-06-07 16-07",
    "id": "console-single-shot-001",
    "priority": 1,
    "area": "console app",
    "title": "Single-shot console agent",
    "user_visible_behavior": "Users run one-agent with a single quoted prompt and receive one final non-streaming answer.",
    "status": "passing",
    "verification": [
      "CLI accepts a prompt argument such as `one-agent \"Explain this task\"`.",
      "The app performs one run per invocation and does not keep multi-turn conversation state.",
      "The app prints only the final answer to stdout on success.",
      "Errors are printed to stderr and return a nonzero exit code."
    ],
    "evidence": [
      "24 pytest tests pass: 6 CLI tests (valid prompt, whitespace strip, no args, multi args, blank, empty), 4 runtime tests (response return, api_key pass-through, api_key omission, model/base_url), 4 main integration tests (stdout output, CliError stderr, ConfigError stderr, unexpected error stderr), 10 config tests.",
      "main.py accepts exactly one prompt argument, calls LLM via ChatOpenAI, prints answer to stdout.",
      "CliError, ConfigError, and unexpected exceptions all print to stderr and exit(1).",
      "Single-shot: one invoke() call per run, no conversation state retained."
    ],
    "notes": "The agent may perform internal multi-step reasoning and tool calls before producing the final answer, but the user experience remains single-shot and non-streaming."
  },
  {
    "last_updated": "2026-06-07 13-51",
    "id": "openai-compatible-llm-002",
    "priority": 1,
    "area": "llm integration",
    "title": "OpenAI-compatible model configuration",
    "user_visible_behavior": "Users configure the model with OpenAI-compatible environment variables or a `.env` file.",
    "status": "passing",
    "verification": [
      "The app loads configuration from environment variables and `.env`.",
      "`OPENAI_API_KEY`, `OPENAI_BASE_URL`, and `OPENAI_MODEL` configure the chat model.",
      "The app fails fast when required model configuration is missing.",
      "No non-OpenAI-compatible provider-specific configuration is required."
    ],
    "evidence": [
      "10 pytest tests pass covering: load all vars, whitespace stripping, missing required vars (parametrized), all required missing, blank required var, optional API key (absent → None, blank → None), dataclass fields, frozen immutability.",
      "main.py prints config on success (exit 0), prints error to stderr on missing config (exit 1).",
      "Package renamed from my_package to one_agent per architecture spec.",
      "OPENAI_API_KEY is optional; when absent, Entra ID auth is assumed."
    ],
    "notes": "Do not spend heavy test effort on env configuration beyond basic success and missing-config behavior."
  },
  {
    "last_updated": "2026-06-07 13-09",
    "id": "mention-parser-003",
    "priority": 1,
    "area": "prompt routing",
    "title": "Explicit skill and MCP mention parsing",
    "user_visible_behavior": "Users opt into skills with `@skill-name` and MCP servers with `/mcp-name` anywhere in the prompt.",
    "status": "not_started",
    "verification": [
      "Mentions are recognized anywhere in the prompt.",
      "Skill and MCP names may contain letters, numbers, `_`, and `-`.",
      "`@` in the middle of a string, such as an email address, does not trigger skill loading.",
      "Paths or strings with multiple `/` separators do not trigger MCP loading.",
      "Routing mentions are stripped before the task is sent to the model.",
      "The app fails fast if the remaining task is empty after stripping mentions.",
      "Unknown skill or MCP mentions fail fast with a clear error."
    ],
    "evidence": [],
    "notes": "Only explicitly mentioned skills and MCP servers are loaded. If no mentions are present, no skills or MCP tools are loaded."
  },
  {
    "last_updated": "2026-06-07 13-09",
    "id": "claude-skills-004",
    "priority": 1,
    "area": "skills",
    "title": "Claude-style skill loading",
    "user_visible_behavior": "Users place skills under `~/.claude/skills/<skill-name>/SKILL.md` and reference them with `@skill-name`.",
    "status": "not_started",
    "verification": [
      "Skill names match folder names exactly.",
      "The app loads `SKILL.md` from each explicitly mentioned skill folder.",
      "Multiple skills are loaded in mention order and added to agent context with clear boundaries.",
      "Missing folders or missing `SKILL.md` files fail fast.",
      "Sibling files or executable scripts in skill folders are not loaded or registered as tools in v1."
    ],
    "evidence": [],
    "notes": "Skills are instructions only for v1. MCP is the only tool mechanism."
  },
  {
    "last_updated": "2026-06-07 13-09",
    "id": "claude-mcp-005",
    "priority": 1,
    "area": "mcp",
    "title": "Claude-compatible MCP server loading",
    "user_visible_behavior": "Users configure MCP servers in `~/.claude.json` and reference a server with `/mcp-name`.",
    "status": "not_started",
    "verification": [
      "The app reads a top-level `mcpServers` object from `~/.claude.json`.",
      "`/mcp-name` maps to an MCP server name, not an individual tool name.",
      "Only command-based stdio MCP servers are supported in v1.",
      "All tools exposed by an explicitly mentioned MCP server are made available to the agent for that run.",
      "The agent decides which exposed tools to call.",
      "MCP server startup or connection failure fails the run.",
      "The app does not implement reusable MCP daemon lifecycle management in v1."
    ],
    "evidence": [],
    "notes": "The expected config shape is compatible with Claude-style `mcpServers`, for example command, args, and env per server. Implementations should follow the MCP client library lifecycle and avoid orphaned child processes."
  },
  {
    "last_updated": "2026-06-07 13-09",
    "id": "langchain-langgraph-agent-006",
    "priority": 2,
    "area": "agent runtime",
    "title": "LangChain and LangGraph agent runtime",
    "user_visible_behavior": "The console app answers prompts using a LangChain/LangGraph agent that can use explicitly loaded skills and MCP tools.",
    "status": "not_started",
    "verification": [
      "The runtime builds the model, selected skill context, and selected MCP tools into a single agent run.",
      "The agent can perform multiple internal tool calls before returning one final answer.",
      "The runtime does not load unmentioned skills or MCP servers."
    ],
    "evidence": [],
    "notes": "Use LangChain, LangGraph, and LangSmith SDKs as the AI agent framework."
  },
  {
    "last_updated": "2026-06-07 13-09",
    "id": "langsmith-tracing-007",
    "priority": 3,
    "area": "observability",
    "title": "Optional LangSmith tracing",
    "user_visible_behavior": "Tracing is enabled automatically when LangSmith credentials are configured and otherwise stays off.",
    "status": "not_started",
    "verification": [
      "Tracing is enabled when a LangSmith API key is present.",
      "Tracing is disabled when no LangSmith API key is present.",
      "The app runs successfully without LangSmith configuration."
    ],
    "evidence": [],
    "notes": "Use the conventional LangSmith environment variables supported by the LangChain/LangSmith SDKs."
  }
]
```
