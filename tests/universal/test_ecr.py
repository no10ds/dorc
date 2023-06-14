import pytest
import pulumi

from mock import patch, call, ANY
from infrastructure.universal.ecr import CreateEcrResource
from infrastructure.universal.creator import CreateUniversal


class TestCreateEcrResource:
    @pytest.mark.usefixtures("mock_pulumi", "mock_pulumi_config", "universal_config")
    @pytest.fixture
    def universal_infrastructure_block(
        self, mock_pulumi, mock_pulumi_config, universal_config
    ):
        universal_infra_block = CreateUniversal(universal_config)
        return universal_infra_block

    @pytest.mark.usefixtures("universal_infrastructure_block")
    @pytest.fixture
    def ecr_resource_block(self, universal_infrastructure_block) -> CreateEcrResource:
        ecr_resource_block = CreateEcrResource(
            config=universal_infrastructure_block.config,
            aws_provider=universal_infrastructure_block.aws_provider,
            repo_name="test-repo",
        )
        return ecr_resource_block

    @pytest.mark.usefixtures("ecr_resource_block", "universal_config")
    def test_instantiate_create_ecr_resource(
        self, ecr_resource_block, universal_config
    ):
        assert ecr_resource_block.config == universal_config
        assert ecr_resource_block.repo_name == "test-repo"

    @pytest.mark.usefixtures("ecr_resource_block")
    @pulumi.runtime.test
    def test_ecr_repository_created(self, ecr_resource_block: CreateEcrResource):
        def check_repo(args):
            name, force_delete, encryption = args
            assert name == "test-pipelines-test-repo"
            assert force_delete is True
            assert encryption == [{"encryption_type": "KMS"}]

        ecr_repo = ecr_resource_block.apply().ecr_repo
        return pulumi.Output.all(
            ecr_repo.name, ecr_repo.force_delete, ecr_repo.encryption_configurations
        ).apply(check_repo)

    @pytest.mark.usefixtures("ecr_resource_block")
    @patch("pulumi.export")
    def test_ecr_exports(
        self, pulumi_export: patch, ecr_resource_block: CreateEcrResource
    ):
        ecr_resource_block.export()
        assert pulumi_export.call_args_list == [
            call("ecr-repository-test-repo-arn", ANY),
            call("ecr-repository-test-repo-id", ANY),
            call("ecr-repository-test-repo-url", ANY),
        ]
