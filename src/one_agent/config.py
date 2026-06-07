"""Environment variable loading and validation for one-agent."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    """Validated configuration loaded from environment variables.

    When ``openai_api_key`` is None, Entra ID (Azure DefaultAzureCredential)
    is used for LLM endpoint authentication.
    """

    openai_api_key: str | None
    openai_base_url: str
    openai_model: str


class ConfigError(Exception):
    """Raised when required configuration is missing or invalid."""


def load_config() -> Config:
    """Load and validate OpenAI-compatible configuration from env vars and .env.

    Reads ``OPENAI_BASE_URL`` and ``OPENAI_MODEL`` (required) and
    ``OPENAI_API_KEY`` (optional) from the environment (with ``.env``
    fallback).  When the API key is absent, the app assumes Entra ID
    authentication will be used.
    """
    load_dotenv()

    required = ("OPENAI_BASE_URL", "OPENAI_MODEL")
    missing = [name for name in required if not os.environ.get(name, "").strip()]

    if missing:
        names = ", ".join(missing)
        raise ConfigError(
            f"Missing required environment variable(s): {names}. "
            "Set them in the environment or in a .env file."
        )

    raw_key = os.environ.get("OPENAI_API_KEY", "").strip() or None

    return Config(
        openai_api_key=raw_key,
        openai_base_url=os.environ["OPENAI_BASE_URL"].strip(),
        openai_model=os.environ["OPENAI_MODEL"].strip(),
    )
