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
    "last_updated": "2026-06-08 08-35",
    "id": "mention-parser-003",
    "priority": 1,
    "area": "prompt routing",
    "title": "Explicit skill and MCP mention parsing",
    "user_visible_behavior": "Users opt into skills with `@skill-name` and MCP servers with `/mcp-name` anywhere in the prompt.",
    "status": "passing",
    "verification": [
      "Mentions are recognized anywhere in the prompt.",
      "Skill and MCP names may contain letters, numbers, `_`, and `-`.",
      "`@` in the middle of a string, such as an email address, does not trigger skill loading.",
      "Paths or strings with multiple `/` separators do not trigger MCP loading.",
      "Routing mentions are stripped before the task is sent to the model.",
      "The app fails fast if the remaining task is empty after stripping mentions.",
      "Unknown skill or MCP mentions fail fast with a clear error."
    ],
    "evidence": [
      "54 pytest tests pass (17 new in test_mentions.py + 2 new in test_main.py).",
      "src/one_agent/mentions.py exposes parse_mentions, validate_mentions, ParsedPrompt, MentionError.",
      "Regex uses leading whitespace/start-of-string boundary so user@example.com and /etc/hosts do not match.",
      "main.py calls parse_mentions then validate_mentions(known_skills=(), known_mcps=()); since loaders are not yet implemented, any mention currently fails fast with a MentionError listing the offending @name or /name.",
      "Empty task after stripping raises MentionError with 'no task text remains' guidance; stripped task is what gets sent to invoke()."
    ],
    "notes": "Validation uses caller-supplied known-name sets so the skills (004) and MCP (005) features can wire in real loader output without changing this module."
  },
  {
    "last_updated": "2026-06-08 09-10",
    "id": "claude-skills-004",
    "priority": 1,
    "area": "skills",
    "title": "Claude-style skill loading",
    "user_visible_behavior": "Users place skills under `~/.claude/skills/<skill-name>/SKILL.md` and reference them with `@skill-name`.",
    "status": "passing",
    "verification": [
      "Skill names match folder names exactly.",
      "The app loads `SKILL.md` from each explicitly mentioned skill folder.",
      "Multiple skills are loaded in mention order and added to agent context with clear boundaries.",
      "Missing folders or missing `SKILL.md` files fail fast.",
      "Sibling files or executable scripts in skill folders are not loaded or registered as tools in v1."
    ],
    "evidence": [
      "73 pytest tests pass (12 new in test_skills.py, 2 new in test_main.py, 2 new in test_runtime.py, 1 new in test_mentions.py).",
      "src/one_agent/skills.py exposes Skill, SkillError, default_skills_dir, discover_skills, load_skills, format_skills_context.",
      "discover_skills lists immediate subfolders of ~/.claude/skills containing SKILL.md; load_skills enforces exact-case match against iterdir() entries so case-insensitive filesystems (Windows) still reject @Writer vs writer.",
      "Missing folder and missing SKILL.md each raise SkillError with the offending @name and expected path.",
      "Only SKILL.md is read; sibling files and scripts are ignored (test_sibling_files_are_not_loaded).",
      "format_skills_context wraps each skill in BEGIN/END markers tagged with a per-call random token so user content cannot forge a closing boundary.",
      "main.py wires discover_skills → validate_mentions(known_skills=...) → load_skills → format_skills_context → invoke(system_instructions=...).",
      "runtime.invoke gained optional system_instructions param; sends as preceding system message when non-empty.",
      "validate_mentions now suggests the canonical skill name on case-mismatch (Windows-friendly error).",
      "PR Review agent run; addressed boundary-forgeability and case-mismatch hint findings."
    ],
    "notes": "Skills are instructions only for v1. MCP is the only tool mechanism."
  },
  {
    "last_updated": "2026-06-08 10-30",
    "id": "claude-mcp-005",
    "priority": 1,
    "area": "mcp",
    "title": "Claude-compatible MCP server loading",
    "user_visible_behavior": "Users configure MCP servers in `~/.claude.json` and reference a server with `/mcp-name`.",
    "status": "passing",
    "verification": [
      "The app reads a top-level `mcpServers` object from `~/.claude.json`.",
      "`/mcp-name` maps to an MCP server name, not an individual tool name.",
      "Only command-based stdio MCP servers are supported in v1.",
      "All tools exposed by an explicitly mentioned MCP server are made available to the agent for that run.",
      "The agent decides which exposed tools to call.",
      "MCP server startup or connection failure fails the run.",
      "The app does not implement reusable MCP daemon lifecycle management in v1."
    ],
    "evidence": [
      "100 pytest tests pass (15 new in test_mcp_config.py, 5 new in test_mcp_servers.py, 3 new in test_runtime.py, 4 new in test_main.py).",
      "src/one_agent/mcp_config.py exposes McpServer, McpConfigError, default_mcp_config_path, load_mcp_config; rejects entries lacking a string `command`, with non-string args/env values, or with a transport/type other than 'stdio'.",
      "src/one_agent/mcp_servers.py exposes McpServerError, to_stdio_connection, load_mcp_tools; load_mcp_tools wraps MultiServerMCPClient.get_tools() and re-raises lifecycle errors (OSError/RuntimeError/ConnectionError) as McpServerError with the offending server name(s) and exception type.",
      "runtime.invoke gained mcp_servers param; when non-empty, lists tools and runs a LangGraph create_react_agent in a single asyncio.run so adapter sessions stay alive across tool calls; tool listing is bounded by a 30s timeout that raises McpServerError on hang.",
      "main.py wires load_mcp_config (lazy: only loaded when ≥1 /mcp mention) → validate_mentions(known_mcps=...) → invoke(mcp_servers=...).",
      "Malformed ~/.claude.json does not break runs that don't mention an MCP server (test_malformed_mcp_config_does_not_block_runs_without_mcp_mention).",
      "Unknown /mcp mention fails fast via validate_mentions.",
      "PR Review agent run; addressed findings #1 (lazy MCP load), #2 (listing timeout), #3 (single event loop for listing + agent), #5 (narrowed except in load_mcp_tools)."
    ],
    "notes": "The expected config shape is compatible with Claude-style `mcpServers`, for example command, args, and env per server. Implementations should follow the MCP client library lifecycle and avoid orphaned child processes. Real-subprocess integration tests deferred — current tests mock MultiServerMCPClient. Stderr from MCP child processes still goes to the user's terminal (langchain-mcp-adapters does not currently expose per-server errlog)."
  },
  {
    "last_updated": "2026-06-09 10-30",
    "id": "langchain-langgraph-agent-006",
    "priority": 2,
    "area": "agent runtime",
    "title": "LangChain and LangGraph agent runtime",
    "user_visible_behavior": "The console app answers prompts using a LangChain/LangGraph agent that can use explicitly loaded skills and MCP tools.",
    "status": "passing",
    "verification": [
      "The runtime builds the model, selected skill context, and selected MCP tools into a single agent run.",
      "The agent can perform multiple internal tool calls before returning one final answer.",
      "The runtime does not load unmentioned skills or MCP servers."
    ],
    "evidence": [
      "runtime.invoke always runs the LangChain agent on the async path via asyncio.run; MCP tools are loaded only when /mcp servers are explicitly selected.",
      "test_runtime.py covers no-MCP agent run, MCP tool wiring, and multi-tool-call final-message behavior; full suite (104 tests) passes with ruff clean.",
      "Framework deps satisfied via langchain (re-exports create_agent from langgraph) and langchain-mcp-adapters; no direct langgraph/langsmith imports needed."
    ],
    "notes": "Single-shot at the CLI boundary. LangSmith tracing is owned by feature 007."
  },
  {
    "last_updated": "2026-06-09 12-42",
    "id": "langsmith-tracing-007",
    "priority": 3,
    "area": "observability",
    "title": "Optional LangSmith tracing",
    "user_visible_behavior": "Tracing is enabled automatically when LangSmith credentials are configured and otherwise stays off.",
    "status": "passing",
    "verification": [
      "Tracing is enabled when a LangSmith API key is present.",
      "Tracing is disabled when no LangSmith API key is present.",
      "The app runs successfully without LangSmith configuration."
    ],
    "evidence": [
      "116 pytest tests pass (10 new in test_tracing.py, 2 new in test_main.py); ruff check + format clean.",
      "src/one_agent/tracing.py exposes TracingConfig and configure_tracing; reads LANGSMITH_API_KEY (legacy LANGCHAIN_API_KEY honored) and the LANGSMITH_TRACING / legacy LANGCHAIN_TRACING_V2 on/off override.",
      "When a key is present and tracing isn't explicitly disabled, both LANGSMITH_TRACING and LANGCHAIN_TRACING_V2 are set to 'true' so the LangChain SDK exports traces automatically (langsmith 0.8.9 is already a transitive dep of langchain).",
      "When no key is present (or override is false), both flags are normalized to 'false' so a stale LANGSMITH_TRACING=true left in the shell does not cause unauthenticated exports.",
      "main.py calls configure_tracing() after load_config() so .env values are visible; integration test test_run_succeeds_without_langsmith_config asserts the app works without any LangSmith vars.",
      ".env.sample and README.md document the optional LangSmith vars and the LANGSMITH_TRACING=false kill switch.",
      "PR Review agent run; addressed findings #1 (legacy LANGCHAIN_TRACING_V2 disable honored), #2 (stale-flag normalization), #3 (dropped speculative project/endpoint fields), #4 (added coverage for legacy-disable and stale-true paths)."
    ],
    "notes": "Use the conventional LangSmith environment variables supported by the LangChain/LangSmith SDKs."
  }
]
```
