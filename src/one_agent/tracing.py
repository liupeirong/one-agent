"""Optional LangSmith tracing configuration for one-agent.

Tracing is enabled automatically when a LangSmith API key is present in
the environment and stays off otherwise. The LangChain SDK reads the
LangSmith environment variables itself, so this module only inspects the
environment and normalizes the ``LANGSMITH_TRACING`` /
``LANGCHAIN_TRACING_V2`` flags so the SDK sees a consistent on/off
state.

Recognized environment variables (per LangSmith SDK conventions):

* ``LANGSMITH_API_KEY`` -- API key for the LangSmith project. Legacy
  ``LANGCHAIN_API_KEY`` is also honored.
* ``LANGSMITH_TRACING`` / legacy ``LANGCHAIN_TRACING_V2`` -- explicit
  on/off override. When either is set to a falsy value (``"false"``,
  ``"0"``, ``"no"``, ``"off"``), tracing stays disabled even if a key
  is present.
"""

import os
from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass

_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})
_FALSE_VALUES = frozenset({"0", "false", "no", "off"})
_TRACING_FLAGS = ("LANGSMITH_TRACING", "LANGCHAIN_TRACING_V2")


@dataclass(frozen=True)
class TracingConfig:
    """Resolved LangSmith tracing state for a single run."""

    enabled: bool


def configure_tracing(
    env: MutableMapping[str, str] | None = None,
) -> TracingConfig:
    """Enable LangSmith tracing when an API key is configured.

    Reads the LangSmith environment variables from *env* (defaults to
    ``os.environ``). When an API key is present and tracing is not
    explicitly disabled (via ``LANGSMITH_TRACING`` or legacy
    ``LANGCHAIN_TRACING_V2``), sets both flags to ``"true"`` so the
    LangChain SDK begins exporting traces. Otherwise normalizes both
    flags to ``"false"`` so a stale ``LANGSMITH_TRACING=true`` left in
    the shell does not cause the SDK to attempt unauthenticated
    exports.
    """
    target: MutableMapping[str, str] = os.environ if env is None else env

    api_key = _get_first_value(target, ("LANGSMITH_API_KEY", "LANGCHAIN_API_KEY"))
    explicit = _parse_bool(_get_first_value(target, _TRACING_FLAGS))

    if not api_key or explicit is False:
        for flag in _TRACING_FLAGS:
            if flag in target:
                target[flag] = "false"
        return TracingConfig(enabled=False)

    for flag in _TRACING_FLAGS:
        target[flag] = "true"
    return TracingConfig(enabled=True)


def _get_first_value(env: Mapping[str, str], names: tuple[str, ...]) -> str | None:
    """Return the first non-blank value in *env* matching any of *names*."""
    for name in names:
        value = env.get(name, "").strip()
        if value:
            return value
    return None


def _parse_bool(raw: str | None) -> bool | None:
    """Parse a tri-state boolean env value (True/False/None)."""
    if raw is None:
        return None
    normalized = raw.strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    return None
