# Progress Log

> Append session logs conforming to this TypeScript schema:
interface session_log {
    datetime: string; // session start datetime YYYY-MM-DD HH-mm
    current_feature: string; // which feature is worked on in this session?
    what_was_done: string[]; // what's implemented, tested, bugs fixed etc
    decision: string[]; // what decisions were made, changed
    issues: string[]; // what issues were encountered, what's their status now
    benchmark_results?: Record<string, string>; // performance benchmark numbers if any, ex. {Query_What_is_the_architecture: "~250ms with 2 citations"}
    next_step: string;
}[]

```json
[
  {
    "datetime": "2026-06-09 12-42",
    "current_feature": "langsmith-tracing-007",
    "what_was_done": [
      "Added src/one_agent/tracing.py with TracingConfig and configure_tracing; pure env inspection that normalizes LANGSMITH_TRACING and legacy LANGCHAIN_TRACING_V2 to 'true' when a key is present, 'false' otherwise.",
      "Wired main.py to call configure_tracing() after load_config(); exported symbols from one_agent.__init__.",
      "Documented optional LangSmith env vars in .env.sample and README.md.",
      "Added tests/test_tracing.py (10 tests) and 2 new integration tests in test_main.py covering with-key and without-key paths; test_main fixture now clears LangSmith env vars by default.",
      "116 pytest tests pass; ruff check + format clean.",
      "PR Review agent run; addressed findings #1 (legacy LANGCHAIN_TRACING_V2 disable), #2 (stale-flag normalization), #3 (dropped unused project/endpoint fields), #4 (added coverage for legacy-disable and stale-true)."
    ],
    "decision": [
      "No new direct dependency: langsmith 0.8.9 is already a transitive dep of langchain, and the SDK auto-exports when the tracing flags are set.",
      "Normalize both LANGSMITH_TRACING and legacy LANGCHAIN_TRACING_V2 on every run (set to 'true' when enabled, 'false' when disabled) so downstream SDK code sees a consistent state regardless of what the shell exported.",
      "Honor both flags as the explicit on/off override so users migrating from legacy LangChain tracing can keep their existing kill switch.",
      "Keep TracingConfig minimal (just `enabled`) per python-standards.instructions.md — don't expose project/endpoint until a concrete consumer needs them."
    ],
    "issues": [
      "No live LangSmith integration test (would require real credentials and external network); covered by unit tests on the env-mutation contract instead.",
      "sys.path.insert hack remains in main.py and test files (low priority, unchanged)."
    ],
    "next_step": "Feature list 007 complete; remaining items in .ai/feature-list.md are all 'passing'. Pick up new features in a future session."
  },
  {
    "datetime": "2026-06-09 08-51",
    "current_feature": "langchain-langgraph-agent-006",
    "what_was_done": [
      "Unified runtime.invoke on a single async agent path via asyncio.run; no-MCP runs use an empty tool list, MCP runs load tools from selected servers in the same event loop.",
      "Added/updated test_runtime.py for no-MCP agent execution, MCP tool wiring, and multi-tool-call final-message behavior; 104 tests pass, ruff clean.",
      "Split README into User Guide and Developer Guide; switched Windows code blocks to cmd.",
      "Added CLAUDE.md rule: do not commit or push; leave changes for the user to review.",
      "Marked feature 006 passing in .ai/feature-list.md with evidence."
    ],
    "decision": [
      "Always run the agent through asyncio.run (CLI entrypoint is sync, so no nested-loop risk).",
      "Do not add direct langgraph/langsmith deps: create_agent is re-exported via langchain; langsmith tracing belongs to feature 007."
    ],
    "issues": [
      "Real-subprocess MCP integration tests still deferred (mocked)."
    ],
    "next_step": "Implement langsmith-tracing-007."
  },
  {
    "datetime": "2026-06-08 10-21",
    "current_feature": "claude-mcp-005",
    "what_was_done": [
      "Created src/one_agent/mcp_config.py with McpServer, McpConfigError, default_mcp_config_path, load_mcp_config — parses ~/.claude.json and validates each mcpServers entry (string command, list-of-string args, dict[str,str] env, transport must be 'stdio' if present).",
      "Created src/one_agent/mcp_servers.py with McpServerError, to_stdio_connection, load_mcp_tools — sync wrapper around langchain_mcp_adapters.MultiServerMCPClient.get_tools().",
      "Extended runtime.invoke with mcp_servers kwarg; when non-empty, lists tools and runs LangGraph create_react_agent in a single asyncio.run (single event loop for listing + agent). Tool listing bounded by a 30s timeout that raises McpServerError.",
      "Wired main.py: load_mcp_config is now called only when parsed.mcps is non-empty → validate_mentions(known_mcps=...) → invoke(mcp_servers=...).",
      "Added langchain-mcp-adapters and langgraph to pyproject.toml.",
      "Exported new symbols from src/one_agent/__init__.py.",
      "Added tests/test_mcp_config.py (15 tests), tests/test_mcp_servers.py (5 tests), 3 new in test_runtime.py (mcp_servers triggers agent, no-mcp uses plain path, startup failure raises), 4 new in test_main.py (mcp passed through, unknown /mcp fails, bad config fails when mentioned, bad config does NOT block runs without /mcp).",
      "All 100 pytest tests pass; ruff check + format clean.",
      "PR Review agent run; addressed findings #1 (lazy MCP config load), #2 (listing timeout), #3 (single event loop), #5 (narrowed except in load_mcp_tools)."
    ],
    "decision": [
      "~/.claude.json is owned by the Claude CLI, so one-agent reads it only when the user actually mentions a /mcp server. Malformed-config runs that don't ask for MCP are not blocked.",
      "Both tool listing and agent invocation run inside one asyncio.run. Eliminates the cross-loop assumption with langchain-mcp-adapters' per-call session model and lets future versions switch to long-lived sessions without changing one-agent.",
      "30s timeout on get_tools() prevents a misconfigured or hung MCP server from blocking the console indefinitely (which is also the most realistic orphaned-child-process scenario).",
      "load_mcp_tools is kept as a sync utility but is not used by main.py; runtime owns the end-to-end async path.",
      "Narrowed the wrap-as-McpServerError except to OSError/RuntimeError/ConnectionError plus asyncio.TimeoutError so programmer bugs (TypeError, etc.) surface as themselves."
    ],
    "issues": [
      "MCP child-process stderr still goes to the user's terminal — langchain-mcp-adapters does not expose per-server errlog. Documented as a known limitation; could be addressed by upstream change or subprocess wrapper.",
      "No real-subprocess integration test for MCP yet; all tests mock MultiServerMCPClient. Worth adding later (PR Review finding #6, deferred).",
      "Windows-specific `npx` vs `npx.cmd` resolution is a likely first user-support issue but is upstream/user-config concern.",
      "sys.path.insert hack remains in main.py and test files (low priority)."
    ],
    "next_step": "Implement langchain-langgraph-agent-006 (formalize the LangChain/LangGraph runtime that the agent path already uses) or langsmith-tracing-007."
  },
  {
    "datetime": "2026-06-08 09-04",
    "current_feature": "claude-skills-004",
    "what_was_done": [
      "Created src/one_agent/skills.py with Skill dataclass, SkillError, default_skills_dir, discover_skills, load_skills, format_skills_context.",
      "discover_skills returns immediate subfolders of ~/.claude/skills containing SKILL.md, sorted for determinism; returns () when the dir is missing.",
      "load_skills validates each name against iterdir() entries (case-exact even on case-insensitive FS), reads SKILL.md as utf-8, raises SkillError on missing folder / missing file / OSError.",
      "format_skills_context wraps each skill in BEGIN/END markers tagged with a per-call secrets.token_hex(8) token so user content cannot forge a closing boundary.",
      "Extended runtime.invoke with optional system_instructions kwarg; when non-empty it is sent as a preceding ('system', ...) message via ChatOpenAI.",
      "Wired main.py: discover_skills → validate_mentions(known_skills=...) → load_skills → format_skills_context → invoke(system_instructions=...).",
      "Added case-mismatch hint to validate_mentions ('did you mean @writer?') so Windows users get a clear error.",
      "Added tests/test_skills.py (12 tests), 2 new tests in test_main.py (skill loaded into system_instructions, no mention → None), 2 new in test_runtime.py (system message wiring, empty-string fallback), 1 new in test_mentions.py (case-mismatch hint).",
      "Updated test_main.py fixture to monkeypatch Path.home to a tmp dir so real ~/.claude/skills doesn't leak.",
      "All 73 pytest tests pass.",
      "PR Review agent run; addressed both 🟡 findings (boundary forgeability and Windows case-mismatch error UX)."
    ],
    "decision": [
      "Enforce case-exact skill names by checking against iterdir() entries (Windows FS is case-insensitive, so folder.is_dir() alone is insufficient).",
      "Use per-call random token in skill boundary markers instead of a static sentinel to prevent prompt-injection escape from user-authored SKILL.md.",
      "Send skill context as a 'system' message rather than prepended to the human prompt — keeps the user's task text clean and matches LangChain conventions.",
      "format_skills_context returns '' (not None) for the empty case; main.py converts '' → None before passing to invoke so the runtime can branch cleanly.",
      "MCP loader still not implemented, so main.py keeps known_mcps=() — any /mcp mention still fails fast."
    ],
    "issues": [
      "MCP server loading (claude-mcp-005) still not implemented; any /mcp mention currently fails fast.",
      "SKILL.md YAML frontmatter (if present) is sent verbatim to the model — noted as a possible follow-up but not in v1 scope.",
      "sys.path.insert hack remains in main.py and test files (low priority)."
    ],
    "next_step": "Implement claude-mcp-005 (Claude-compatible MCP server loading) so /mcp mentions can resolve to real stdio servers."
  },
    "datetime": "2026-06-08 08-31",
    "current_feature": "mention-parser-003",
    "what_was_done": [
      "Created src/one_agent/mentions.py with parse_mentions, validate_mentions, ParsedPrompt, MentionError.",
      "Regex uses negative lookbehind/lookahead on [\\w@] / [\\w/] so user@example.com and /etc/hosts are skipped while quoted/bracketed mentions still match.",
      "Whitespace is collapsed and orphaned punctuation glued back after stripping mentions.",
      "Exposed the new symbols from src/one_agent/__init__.py.",
      "Wired main.py to parse_mentions then validate_mentions (with empty known sets) before load_config/invoke so routing errors fail fast.",
      "Added tests/test_mentions.py with 18 cases covering all verification items, plus 2 main.py tests for unknown-mention and empty-task-after-mentions paths.",
      "All 55 pytest tests pass.",
      "PR Review agent run; addressed findings #1 (quoted/bracketed mentions) and #3 (dangling punctuation)."
    ],
    "decision": [
      "validate_mentions takes caller-supplied known_skills/known_mcps sets so the upcoming skill (004) and MCP (005) loaders can wire in real names without changing this module.",
      "Until loaders ship, main.py passes empty known sets, which is the correct behaviour: any explicit mention is currently 'unknown' and fails fast with a clear message.",
      "Empty-task validation is checked before unknown-mention validation; users get the most fundamental error first."
    ],
    "issues": [
      "Skills (004) and MCP (005) loaders not yet implemented, so any prompt with mentions fails until those land. This is expected and documented.",
      "sys.path.insert hack remains in main.py and tests (unchanged, low priority)."
    ],
    "next_step": "Implement claude-skills-004 (Claude-style SKILL.md loading) so mention parsing can resolve to real skill instructions."
  },
  {
    "datetime": "2026-06-07 13-09",
    "current_feature": "feature planning documentation",
    "what_was_done": [
      "Recorded the agreed v1 product scope in .ai/feature-list.md.",
      "Updated docs/ARCHITECTURE.md with the console app architecture, configuration conventions, prompt routing rules, MCP behavior, testing strategy, observability, and security boundaries.",
      "Updated README.md with concise end-user setup and usage instructions."
    ],
    "decision": [
      "Skills use Claude-style ~/.claude/skills/<skill-name>/SKILL.md folders and are instructions only in v1.",
      "MCP servers are configured in ~/.claude.json under mcpServers and selected by /server-name mentions.",
      "The LLM interface is OpenAI-compatible only, configured by environment variables or .env.",
      "The app is single-shot, non-streaming, and loads no skills or MCP servers unless explicitly mentioned.",
      "LangSmith tracing is optional and enabled only when credentials are configured."
    ],
    "issues": [
      "No implementation has started yet; all feature statuses remain not_started.",
      "No unresolved documentation blockers are known."
    ],
    "next_step": "Start implementing the highest-priority unfinished feature from .ai/feature-list.md in a new session."
  },
  {
    "datetime": "2026-06-07 13-51",
    "current_feature": "openai-compatible-llm-002",
    "what_was_done": [
      "Renamed package from my_package to one_agent per architecture spec.",
      "Replaced Azure OpenAI config (AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT) with OpenAI-compatible config (OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL).",
      "Config dataclass is now frozen for immutability.",
      "Added ConfigError exception with actionable error messages listing all missing vars.",
      "Updated main.py to catch ConfigError, print to stderr, and exit nonzero.",
      "Expanded test suite from 3 to 9 tests: parametrized missing var tests, blank var test, frozen test, dotenv isolation.",
      "Fixed test isolation: monkeypatch load_dotenv to prevent .env file from leaking into tests.",
      "PR Review agent ran; finding #1 (test isolation) addressed."
    ],
    "decision": [
      "All three OPENAI vars are required — fail fast if any are missing or blank.",
      "Config is frozen dataclass to prevent accidental mutation.",
      "Tests patch load_dotenv to avoid .env file interference."
    ],
    "issues": [
      "sys.path.insert hack remains in main.py and tests (low priority, will address when adding pyproject.toml scripts entry)."
    ],
    "next_step": "Implement next priority-1 feature: console-single-shot-001 or mention-parser-003."
  },
  {
    "datetime": "2026-06-07 16-07",
    "current_feature": "console-single-shot-001",
    "what_was_done": [
      "Created src/one_agent/cli.py with parse_prompt() for single-argument CLI parsing.",
      "Created src/one_agent/runtime.py with invoke() using ChatOpenAI for single-shot LLM calls.",
      "Updated main.py to accept a prompt argument, call the LLM, and print only the answer to stdout.",
      "Added langchain-openai dependency to pyproject.toml.",
      "Added broad except Exception handler at app boundary for unexpected errors.",
      "Created tests/test_cli.py (6 tests), tests/test_runtime.py (4 tests), tests/test_main.py (4 tests).",
      "Updated .env.sample to use current OPENAI_* variables instead of stale AZURE_OPENAI_* ones.",
      "Updated README.md verify instructions to include prompt argument.",
      "PR Review agent findings addressed: UnboundLocalError fix, sys.argv test isolation, unexpected error test."
    ],
    "decision": [
      "Used langchain-openai (ChatOpenAI) for LLM calls to align with future LangChain/LangGraph agent runtime.",
      "CLI accepts exactly one positional argument (the prompt string).",
      "Unexpected exceptions are caught at app boundary with broad except Exception, printed to stderr, exit(1)."
    ],
    "issues": [
      "sys.path.insert hack remains in main.py and test files (low priority, will address when adding pyproject.toml scripts entry)."
    ],
    "next_step": "Implement next priority-1 feature: mention-parser-003."
  }
]
```
