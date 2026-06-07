"""Unit tests for my_package.config"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from my_package.config import (
    Config,
    load_config,
)


@pytest.fixture(autouse=True)
def isolated_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_DEPLOYMENT", raising=False)


class TestLoadConfig:
    def test_loads_all_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://my.openai.azure.com/")
        monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")

        config = load_config()

        assert config.endpoint == "https://my.openai.azure.com/"
        assert config.deployment == "gpt-4o"

    def test_strips_whitespace_from_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "  https://my.openai.azure.com/  ")
        monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "  gpt-4o  ")

        config = load_config()

        assert config.endpoint == "https://my.openai.azure.com/"
        assert config.deployment == "gpt-4o"


class TestConfig:
    def test_dataclass_fields(self) -> None:
        config = Config(endpoint="https://ep.com", deployment="dep")

        assert config.endpoint == "https://ep.com"
        assert config.deployment == "dep"
        assert not hasattr(config, "langsmith_api_key")
