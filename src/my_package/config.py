"""Environment variable loading and validation one-agent."""

import os
from dataclasses import dataclass


@dataclass
class Config:
    """Validated configuration loaded from environment variables."""

    endpoint: str
    deployment: str


def load_config() -> Config:
    from dotenv import load_dotenv

    load_dotenv()

    return Config(
        endpoint=os.environ["AZURE_OPENAI_ENDPOINT"].strip(),
        deployment=os.environ["AZURE_OPENAI_DEPLOYMENT"].strip(),
    )
