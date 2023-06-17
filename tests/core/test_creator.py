import pytest

from mock import MagicMock, patch
from infrastructure.core.creator import CreatePipeline
from infrastructure.core.models.definition import PipelineDefinition, rAPIdTrigger
from utils.config import Config, rAPIdConfig
from utils.exceptions import InvalidConfigDefinitionException
from utils.constants import (
    LAMBDA_ROLE_ARN,
    STATE_FUNCTION_ROLE_ARN,
    CLOUDEVENT_STATE_MACHINE_TRIGGER_ROLE_ARN,
)


class TestCreatePipeline:
    @pytest.mark.usefixtures(
        "mock_pulumi", "mock_pulumi_config", "config", "pipeline_definition"
    )
    @pytest.fixture
    def pipeline_infrastructure_block(
        self, mock_pulumi, mock_pulumi_config, config, pipeline_definition
    ):
        pipeline_infrastructure_block = CreatePipeline(config, pipeline_definition)
        return pipeline_infrastructure_block

    @pytest.mark.usefixtures("pipeline_infrastructure_block", "config")
    def test_instantiate_pipeline_creator(self, pipeline_infrastructure_block, config):
        assert pipeline_infrastructure_block.config.project == config.project

    @pytest.mark.usefixtures("pipeline_infrastructure_block")
    def test_pipeline_creator_retrieves_lambda_role_arn(
        self, pipeline_infrastructure_block: CreatePipeline
    ):
        mocked_infra_stack_reference = MagicMock()
        pipeline_infrastructure_block.infra_stack_reference = (
            mocked_infra_stack_reference
        )
        mocked_infra_stack_reference.require_output.return_value = "mocked_lambda_arn"

        assert (
            pipeline_infrastructure_block.get_lambda_role_arn() == "mocked_lambda_arn"
        )
        mocked_infra_stack_reference.require_output.assert_called_once_with(
            LAMBDA_ROLE_ARN
        )

    @pytest.mark.usefixtures("pipeline_infrastructure_block")
    def test_pipeline_creator_retrieves_state_machine_role_arn(
        self, pipeline_infrastructure_block: CreatePipeline
    ):
        mocked_infra_stack_reference = MagicMock()
        pipeline_infrastructure_block.infra_stack_reference = (
            mocked_infra_stack_reference
        )
        mocked_infra_stack_reference.require_output.return_value = (
            "mocked_state_machine_arn"
        )

        assert (
            pipeline_infrastructure_block.get_state_machine_role_arn()
            == "mocked_state_machine_arn"
        )
        mocked_infra_stack_reference.require_output.assert_called_once_with(
            STATE_FUNCTION_ROLE_ARN
        )

    @pytest.mark.usefixtures("pipeline_infrastructure_block")
    def test_pipeline_creator_retrieves_cloudevent_trigger_role_arn(
        self, pipeline_infrastructure_block: CreatePipeline
    ):
        mocked_infra_stack_reference = MagicMock()
        pipeline_infrastructure_block.infra_stack_reference = (
            mocked_infra_stack_reference
        )
        mocked_infra_stack_reference.require_output.return_value = (
            "mocked_cloudevent_trigger_arn"
        )

        assert (
            pipeline_infrastructure_block.get_cloudevent_trigger_role_arn()
            == "mocked_cloudevent_trigger_arn"
        )
        mocked_infra_stack_reference.require_output.assert_called_once_with(
            CLOUDEVENT_STATE_MACHINE_TRIGGER_ROLE_ARN
        )

    @pytest.mark.usefixtures("pipeline_infrastructure_block")
    def test_pipeline_creator_fetch_source_directory_name(
        self, pipeline_infrastructure_block: CreatePipeline
    ):
        pipeline_infrastructure_block.pipeline_definition.file_path = (
            "./tests/mock_config_repo_src/test/layer/__main__.py"
        )
        assert (
            pipeline_infrastructure_block.fetch_source_directory_name().rsplit(
                "dorc/tests/", 1
            )[-1]
            == "mock_config_repo_src/test/layer/src"
        )

    @pytest.mark.usefixtures("pipeline_infrastructure_block")
    def test_pipeline_creator_fetch_source_directory_name_with_no_source_code_folder(
        self, pipeline_infrastructure_block: CreatePipeline
    ):
        pipeline_infrastructure_block.pipeline_definition.file_path = (
            "./tests/mock_config_repo_src/src/test/layer/__main__.py"
        )
        pipeline_infrastructure_block.config.universal.source_code_folder = ""

        assert (
            pipeline_infrastructure_block.fetch_source_directory_name().rsplit(
                "dorc/tests/", 1
            )[-1]
            == "mock_config_repo_src/src/test/layer"
        )

    @pytest.mark.usefixtures("pipeline_infrastructure_block")
    def test_fetch_lambda_paths(self, pipeline_infrastructure_block):
        res = pipeline_infrastructure_block.fetch_lambda_paths()
        assert res == ["layer/test/lambda1/lambda.py", "layer/test/lambda2/lambda.py"]

    @pytest.mark.usefixtures(
        "mock_pulumi", "mock_pulumi_config", "config", "pipeline_definition"
    )
    def test_validate_rapid_trigger_fails_with_no_rapid_config(
        self,
        mock_pulumi,
        mock_pulumi_config,
        config: Config,
        pipeline_definition: PipelineDefinition,
    ):
        config.rAPId_config = None
        pipeline_definition.trigger = rAPIdTrigger(domain="domain", name="name")
        with pytest.raises(InvalidConfigDefinitionException):
            CreatePipeline(config, pipeline_definition)

    @pytest.mark.usefixtures(
        "mock_pulumi", "mock_pulumi_config", "config", "pipeline_definition"
    )
    @patch("infrastructure.core.creator.CreateRapidClient")
    def test_create_rapid_client_with_client_key(
        self,
        mock_rapid_client: MagicMock,
        mock_pulumi,
        mock_pulumi_config,
        config: Config,
        pipeline_definition: PipelineDefinition,
    ):
        pipeline_definition.trigger = rAPIdTrigger(
            domain="domain", name="name", client_key="client_key"
        )
        config.rAPId_config = rAPIdConfig(prefix="prefix", user_pool_id="xxx-yyy-zzz")
        mock_rapid_client.return_value.fetch_secret.return_value.user_pool_client = (
            "mock_return"
        )
        pipeline_infrastructure_block = CreatePipeline(config, pipeline_definition)
        assert pipeline_infrastructure_block.create_rapid_client() == "mock_return"

    @pytest.mark.usefixtures(
        "mock_pulumi", "mock_pulumi_config", "config", "pipeline_definition"
    )
    @patch("infrastructure.core.creator.CreateRapidClient")
    def test_create_rapid_client_without_client_key(
        self,
        mock_rapid_client: MagicMock,
        mock_pulumi,
        mock_pulumi_config,
        config: Config,
        pipeline_definition: PipelineDefinition,
    ):
        pipeline_definition.trigger = rAPIdTrigger(domain="domain", name="name")
        config.rAPId_config = rAPIdConfig(prefix="prefix", user_pool_id="xxx-yyy-zzz")
        mock_rapid_client.return_value.outputs.user_pool_client = "mock_return"
        pipeline_infrastructure_block = CreatePipeline(config, pipeline_definition)
        assert pipeline_infrastructure_block.create_rapid_client() == "mock_return"
