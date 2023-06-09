import pytest
from pytest import MonkeyPatch

from utils.exceptions import CannotFindEnvironmentVariableException
from utils.config import UniversalConfig


class TestUniversalConfig:
    def test_cannot_create_universal_config_without_config_repo_env(
        self, monkeypatch: MonkeyPatch
    ):
        monkeypatch.delenv("CONFIG_REPO_PATH", raising=False)
        with pytest.raises(CannotFindEnvironmentVariableException):
            UniversalConfig(
                region="eu-west-2",
                project="test-pipelines",
                tags={"tag": "test"},
            )
