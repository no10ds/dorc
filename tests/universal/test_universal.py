import pytest
import pulumi

from infrastructure.universal import CreateUniversal

from tests.utils import universal_config


class TestCreateUniversal:
    def test_create_universal(self, mock_pulumi, mock_pulumi_config):
        universal_block = CreateUniversal(universal_config)
        assert universal_block.config == universal_config

    def test_retrieve_repo_list_from_folders(self, mock_pulumi, mock_pulumi_config):
        universal_block = CreateUniversal(universal_config)
        assert universal_block.repo_list == ["test-layer"]

    def test_retrieve_repo_list_from_folders_different_source_code_path(
        self, mock_pulumi, mock_pulumi_config
    ):
        universal_config.config_repo_path = "./tests/mock_config_repo"
        universal_config.source_code_path = ""
        universal_block = CreateUniversal(universal_config)
        assert universal_block.repo_list == ["test-layer2"]
