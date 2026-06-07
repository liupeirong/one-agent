"""Console entry point for one-agent."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from one_agent import ConfigError, load_config


def main() -> None:
    try:
        config = load_config()
    except ConfigError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    print(
        f"Config loaded: model={config.openai_model}, base_url={config.openai_base_url}"
    )


if __name__ == "__main__":
    main()
