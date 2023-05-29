import pytest
import os
import pulumi

from pydantic import BaseModel  # pylint: disable=no-name-in-module
from pulumi import Output
from mock import MagicMock, patch
from infrastructure.core.creator import CreatePipeline
from utils.constants import (
    LAMBDA_ROLE_ARN,
    STATE_FUNCTION_ROLE_ARN,
    CLOUDEVENT_STATE_MACHINE_TRIGGER_ROLE_ARN,
)

from tests.utils import config, pipeline_definition, MockedEcrAuthentication


class TestCreatePipeline:
    @pytest.mark.usefixtures("mock_pulumi", "mock_pulumi_config")
    @pytest.fixture
    def pipeline_infrastructure_block(self, mock_pulumi, mock_pulumi_config):
        pipeline_infrastructure_block = CreatePipeline(config, pipeline_definition)
        return pipeline_infrastructure_block

    @pytest.mark.usefixtures("pipeline_infrastructure_block")
    def test_instantiate_pipeline_creator(self, pipeline_infrastructure_block):
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
            "./tests/mock_config_repo_src/src/test/layer/__main__.py"
        )

        assert (
            pipeline_infrastructure_block.fetch_source_directory_name().rsplit(
                "10ds-core-pipelines/tests/", 1
            )[-1]
            == "mock_config_repo_src/src/test/layer/src"
        )

    @pytest.mark.usefixtures("pipeline_infrastructure_block")
    def test_pipeline_creator_fetch_source_directory_name_with_no_source_code_path(
        self, pipeline_infrastructure_block: CreatePipeline
    ):
        pipeline_infrastructure_block.pipeline_definition.file_path = (
            "./tests/mock_config_repo_src/src/test/layer/__main__.py"
        )
        pipeline_infrastructure_block.config.universal.source_code_path = ""

        assert (
            pipeline_infrastructure_block.fetch_source_directory_name().rsplit(
                "10ds-core-pipelines/tests/", 1
            )[-1]
            == "mock_config_repo_src/src/test/layer"
        )

    @pytest.mark.usefixtures("pipeline_infrastructure_block")
    @patch("infrastructure.core.creator.os.walk")
    @patch.object(CreatePipeline, "extract_lambda_name_from_top_dir")
    @patch.object(CreatePipeline, "apply_docker_image_build_and_push")
    @patch.object(CreatePipeline, "apply_lambda_function")
    def test_pipeline_creator_build_and_deploy_folder_structure_functions(
        self,
        mock_apply_lambda: MagicMock,
        mock_apply_docker: MagicMock,
        mock_extract_name: MagicMock,
        mock_os_walk: MagicMock,
        pipeline_infrastructure_block: CreatePipeline,
    ):
        mock_os_walk.return_value = [
            ("/src_dir", ["dir1"], []),
            ("/src_dir/dir1", [], []),
        ]
        mock_extract_name.side_effect = ["lambda1"]
        mock_apply_docker.return_value = "docker_image"
        mock_apply_lambda.return_value.outputs = MagicMock(
            lambda_function="lambda_function"
        )
        pipeline_infrastructure_block.build_and_deploy_folder_structure_functions("url")

        mock_os_walk.assert_called_once_with(pipeline_infrastructure_block.src_dir)
        mock_extract_name.assert_called_once_with("/src_dir/dir1")
        mock_apply_docker.assert_called_once_with("url", "lambda1", "/src_dir/dir1")
        mock_apply_lambda.assert_called_once_with("lambda1", "docker_image")
        assert (
            pipeline_infrastructure_block.created_lambdas["lambda1"]
            == "lambda_function"
        )

    @pytest.mark.usefixtures("pipeline_infrastructure_block")
    @patch("infrastructure.core.creator.dirhash")
    @patch.object(CreatePipeline, "extract_lambda_source_dir_from_top_dir")
    @patch.dict(os.environ, {"CONFIG_REPO_PATH": "10ds-core-pipelines"})
    @pulumi.runtime.test
    def test_pipeline_creator_apply_docker_image_build_and_push(
        self,
        mock_extract_name: MagicMock,
        mock_dirhash: MagicMock,
        pipeline_infrastructure_block: CreatePipeline,
    ):
        def check_built_docker_image(args):
            build, image_name, registry = args
            assert image_name == "test_url:test_lambda_0123abcd"
            assert build == {
                "cacheFrom": {"images": ["test_url:test_lambda_0123abcd"]},
                "args": {"CODE_PATH": "lambda1", "BUILDKIT_INLINE_CACHE": "1"},
                "builderVersion": "BuilderBuildKit",
                "platform": "linux/amd64",
                "context": "10ds-core-pipelines",
                "dockerfile": "10ds-core-pipelines/src/Dockerfile",
            }
            assert registry == {
                "password": "mock_password",
                "server": "test_url",
                "username": "mock_username",
            }

        mock_extract_name.return_value = "lambda1"
        mock_dirhash.return_value = "0123abcd"
        pipeline_infrastructure_block.registry_info = MockedEcrAuthentication(
            password="mock_password", user_name="mock_username"
        )

        image = pipeline_infrastructure_block.apply_docker_image_build_and_push(
            "test_url",
            "test_lambda",
            "",
        )
        return pulumi.Output.all(image.build, image.image_name, image.registry).apply(
            check_built_docker_image
        )
