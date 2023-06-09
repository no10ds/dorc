import os
import pytest

from mock import patch, MagicMock, call
from infrastructure.universal import CreateUniversal
from utils.exceptions import CannotFindEnvironmentVariableException


class TestCreateUniversal:
    @pytest.mark.usefixtures("mock_pulumi", "mock_pulumi_config", "universal_config")
    def test_create_universal(self, mock_pulumi, mock_pulumi_config, universal_config):
        universal_block = CreateUniversal(universal_config)
        assert universal_block.config == universal_config

    @pytest.mark.usefixtures("mock_pulumi", "mock_pulumi_config", "universal_config")
    def test_retrieve_repo_list_from_folders(
        self, mock_pulumi, mock_pulumi_config, universal_config
    ):
        universal_config.source_code_folder = "src"
        universal_block = CreateUniversal(universal_config)
        assert universal_block.repo_list == ["layer-test-lambda1", "layer-test-lambda2"]

    @pytest.mark.usefixtures("mock_pulumi", "mock_pulumi_config", "universal_config")
    @patch("infrastructure.universal.creator.glob")
    def test_retrieve_repo_list_from_folders_with_custom_source_path(
        self, mock_glob, mock_pulumi, mock_pulumi_config, universal_config
    ):
        universal_config.source_code_folder = "app"
        mock_glob.return_value = [
            "layer/test/lambda1/lambda.py",
            "layer/test/lambda2/lambda.py",
        ]
        universal_block = CreateUniversal(universal_config)

        assert universal_block.repo_list == ["layer-test-lambda1", "layer-test-lambda2"]
        mock_glob.assert_called_once_with(
            "./tests/mock_config_repo_src/app/*/*/*/lambda.py"
        )

    @pytest.mark.usefixtures("mock_pulumi", "mock_pulumi_config", "universal_config")
    @patch("infrastructure.universal.creator.CreateEcrResource")
    def test_create_universal_apply(
        self,
        mock_ecr_resource: MagicMock,
        mock_pulumi,
        mock_pulumi_config,
        universal_config,
    ):
        universal_block = CreateUniversal(universal_config)
        repo_list = ["repo1", "repo2"]
        universal_block.repo_list = repo_list
        universal_block.apply()

        mock_ecr_resource.assert_has_calls = [
            call(universal_block.config, universal_block.aws_provider, "repo1"),
            call(universal_block.config, universal_block.aws_provider, "repo2"),
        ]
