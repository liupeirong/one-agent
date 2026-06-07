"""Console entry point for one-agent."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from one_agent import CliError, ConfigError, invoke, load_config, parse_prompt


def main() -> None:
    """Parse a single prompt, call the LLM, and print the answer."""
    try:
        prompt = parse_prompt()
        config = load_config()
        answer = invoke(config=config, prompt=prompt)
    except (CliError, ConfigError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    else:
        print(answer)


if __name__ == "__main__":
    main()
