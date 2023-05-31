import os
import pytest

from mock import patch, MagicMock, call
from infrastructure.universal import CreateUniversal

from tests.utils import universal_config


class TestCreateUniversal:
    @pytest.mark.usefixtures("mock_pulumi", "mock_pulumi_config")
    def test_create_universal(self, mock_pulumi, mock_pulumi_config):
        universal_block = CreateUniversal(universal_config)
        assert universal_block.config == universal_config

    @pytest.mark.usefixtures("mock_pulumi", "mock_pulumi_config")
    @patch.dict(os.environ, {"CONFIG_REPO_PATH": "./tests/mock_config_repo_src"})
    def test_retrieve_repo_list_from_folders(self, mock_pulumi, mock_pulumi_config):
        universal_config.source_code_path = "src"
        universal_block = CreateUniversal(universal_config)
        assert universal_block.repo_list == ["test-layer"]

    @pytest.mark.usefixtures("mock_pulumi", "mock_pulumi_config")
    @patch.dict(os.environ, {"CONFIG_REPO_PATH": "./tests/mock_config_repo"})
    def test_retrieve_repo_list_from_folders_different_source_code_path(
        self, mock_pulumi, mock_pulumi_config
    ):
        universal_config.source_code_path = ""
        universal_block = CreateUniversal(universal_config)
        assert universal_block.repo_list == ["test-layer2"]

    @pytest.mark.usefixtures("mock_pulumi", "mock_pulumi_config")
    @patch("infrastructure.universal.creator.CreateEcrResource")
    def test_create_universal_apply(
        self, mock_ecr_resource: MagicMock, mock_pulumi, mock_pulumi_config
    ):
        universal_block = CreateUniversal(universal_config)
        repo_list = ["repo1", "repo2"]
        universal_block.repo_list = repo_list
        universal_block.apply()

        mock_ecr_resource.assert_has_calls = [
            call(universal_block.config, universal_block.aws_provider, "repo1"),
            call(universal_block.config, universal_block.aws_provider, "repo2"),
        ]
