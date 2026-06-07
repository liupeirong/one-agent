"""Argument parsing and process exit behavior for one-agent."""

import sys


class CliError(Exception):
    """Raised when command-line arguments are invalid."""


def parse_prompt(argv: list[str] | None = None) -> str:
    """Extract the user prompt from command-line arguments.

    Expects exactly one positional argument: the prompt string.
    Returns the stripped prompt text.

    Raises:
        CliError: If no prompt is provided or the prompt is blank.
    """
    args = argv if argv is not None else sys.argv[1:]

    if len(args) == 0:
        raise CliError(
            "Usage: one-agent <prompt>\nProvide a single quoted prompt as the argument."
        )

    if len(args) > 1:
        raise CliError(
            "Expected a single prompt argument. "
            'Wrap multi-word prompts in quotes: one-agent "your prompt here"'
        )

    prompt = args[0].strip()
    if not prompt:
        raise CliError("Prompt cannot be blank.")

    return prompt
