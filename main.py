"""Console entry point for one-agent."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from one_agent import (
    CliError,
    ConfigError,
    McpConfigError,
    McpServerError,
    MentionError,
    SkillError,
    discover_skills,
    format_skills_context,
    invoke,
    load_config,
    load_mcp_config,
    load_skills,
    parse_mentions,
    parse_prompt,
    validate_mentions,
)


def main() -> None:
    """Parse a single prompt, call the LLM, and print the answer."""
    try:
        prompt = parse_prompt()
        parsed = parse_mentions(prompt)
        known_skills = discover_skills()
        # Only touch ~/.claude.json when the user actually mentioned an MCP
        # server. A parse error in a config one-agent doesn't currently
        # need shouldn't break unrelated runs.
        mcp_servers = load_mcp_config() if parsed.mcps else {}
        validate_mentions(
            parsed,
            known_skills=known_skills,
            known_mcps=tuple(mcp_servers.keys()),
        )
        skills = load_skills(parsed.skills)
        skills_context = format_skills_context(skills)
        selected_servers = tuple(mcp_servers[name] for name in parsed.mcps)
        config = load_config()
        answer = invoke(
            config=config,
            prompt=parsed.task,
            system_instructions=skills_context or None,
            mcp_servers=selected_servers or None,
        )
    except (
        CliError,
        ConfigError,
        MentionError,
        SkillError,
        McpConfigError,
        McpServerError,
    ) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    else:
        print(answer)


if __name__ == "__main__":
    main()
