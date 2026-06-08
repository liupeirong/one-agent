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
