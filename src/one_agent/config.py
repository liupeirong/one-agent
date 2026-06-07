"""Environment variable loading and validation for one-agent."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    """Validated configuration loaded from environment variables."""

    openai_api_key: str
    openai_base_url: str
    openai_model: str


class ConfigError(Exception):
    """Raised when required configuration is missing or invalid."""


def load_config() -> Config:
    """Load and validate OpenAI-compatible configuration from env vars and .env.

    Reads ``OPENAI_API_KEY``, ``OPENAI_BASE_URL``, and ``OPENAI_MODEL`` from
    the environment (with ``.env`` fallback).  All three are required; the
    function fails fast with a clear message when any is missing.
    """
    load_dotenv()

    required = ("OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL")
    missing = [name for name in required if not os.environ.get(name, "").strip()]

    if missing:
        names = ", ".join(missing)
        raise ConfigError(
            f"Missing required environment variable(s): {names}. "
            "Set them in the environment or in a .env file."
        )

    return Config(
        openai_api_key=os.environ["OPENAI_API_KEY"].strip(),
        openai_base_url=os.environ["OPENAI_BASE_URL"].strip(),
        openai_model=os.environ["OPENAI_MODEL"].strip(),
    )
