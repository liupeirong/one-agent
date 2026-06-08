"""Console entry point for one-agent."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from one_agent import (
    CliError,
    ConfigError,
    MentionError,
    invoke,
    load_config,
    parse_mentions,
    parse_prompt,
    validate_mentions,
)


def main() -> None:
    """Parse a single prompt, call the LLM, and print the answer."""
    try:
        prompt = parse_prompt()
        parsed = parse_mentions(prompt)
        # Skill and MCP loaders are not yet implemented, so no mentions are
        # currently known. Any mention therefore fails fast with a clear error.
        validate_mentions(parsed, known_skills=(), known_mcps=())
        config = load_config()
        answer = invoke(config=config, prompt=parsed.task)
    except (CliError, ConfigError, MentionError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    else:
        print(answer)


if __name__ == "__main__":
    main()
