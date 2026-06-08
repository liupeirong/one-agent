"""Argument parsing and process exit behavior for one-agent."""

import sys
from pathlib import Path
from typing import TextIO


class CliError(Exception):
    """Raised when command-line arguments are invalid."""


_USAGE = (
    "Usage: one-agent <prompt>\n"
    "       one-agent --file prompt.txt\n"
    "       one-agent < prompt.txt"
)


def parse_prompt(
    argv: list[str] | None = None,
    *,
    stdin: TextIO | None = None,
) -> str:
    """Extract the user prompt from an argument, ``--file``, or stdin.

    Resolution order:
    1. ``--file <path>`` reads the prompt from a file.
    2. A positional argument is used as the prompt.
    3. If stdin is piped/redirected, read from stdin.
    4. Otherwise raise ``CliError``.

    Raises:
        CliError: If no prompt is provided or the prompt is blank.
    """
    args = argv if argv is not None else sys.argv[1:]
    stdin = stdin if stdin is not None else sys.stdin

    prompt = _extract_prompt(args, stdin)

    if not prompt:
        raise CliError("Prompt cannot be blank.")

    return prompt


def _extract_prompt(args: list[str], stdin: TextIO) -> str:
    """Resolve prompt text from args or stdin."""
    if "--file" in args:
        return _read_file_arg(args)

    if len(args) > 1:
        raise CliError(
            "Expected a single prompt argument. "
            'Wrap multi-word prompts in quotes: one-agent "your prompt here"'
        )

    if len(args) == 1:
        return args[0].strip()

    if not stdin.isatty():
        return stdin.read().strip()

    raise CliError(_USAGE)


def _read_file_arg(args: list[str]) -> str:
    """Parse and read the --file argument."""
    idx = args.index("--file")

    if idx + 1 >= len(args):
        raise CliError("--file requires a file path argument.")

    remaining = [a for i, a in enumerate(args) if i not in (idx, idx + 1)]
    if remaining:
        raise CliError("--file cannot be combined with a positional prompt argument.")

    path = Path(args[idx + 1])
    if not path.is_file():
        raise CliError(f"Prompt file not found: {path}")

    return path.read_text(encoding="utf-8").strip()
