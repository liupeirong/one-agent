"""Argument parsing and process exit behavior for one-agent."""

import sys
from typing import TextIO


class CliError(Exception):
    """Raised when command-line arguments are invalid."""


_USAGE = (
    "Usage: one-agent <prompt>\n"
    "       echo <prompt> | one-agent\n"
    "       one-agent < prompt.txt"
)


def parse_prompt(
    argv: list[str] | None = None,
    *,
    stdin: TextIO | None = None,
) -> str:
    """Extract the user prompt from a CLI argument or stdin.

    Resolution order:
    1. If a positional argument is provided, use it.
    2. If no argument and stdin is piped/redirected, read from stdin.
    3. Otherwise raise ``CliError``.

    Raises:
        CliError: If no prompt is provided or the prompt is blank.
    """
    args = argv if argv is not None else sys.argv[1:]
    stdin = stdin if stdin is not None else sys.stdin

    if len(args) > 1:
        raise CliError(
            "Expected a single prompt argument. "
            'Wrap multi-word prompts in quotes: one-agent "your prompt here"'
        )

    if len(args) == 1:
        prompt = args[0].strip()
    elif not stdin.isatty():
        prompt = stdin.read().strip()
    else:
        raise CliError(_USAGE)

    if not prompt:
        raise CliError("Prompt cannot be blank.")

    return prompt
