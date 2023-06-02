from mock import MagicMock, Mock, patch, call, ANY
import pytest
import pulumi

from pulumi_docker import Image
import pulumi_aws as aws
from infrastructure.core._lambda import CreatePipelineLambdaFunction
from infrastructure.core.creator import CreatePipeline

from tests.utils import MockedEcrAuthentication


class TestCreateLambda:
    @pytest.mark.usefixtures(
        "mock_pulumi", "mock_pulumi_config", "config", "pipeline_definition"
    )
    @pytest.fixture
    def pipeline_infrastructure_block(
        self, mock_pulumi, mock_pulumi_config, config, pipeline_definition
    ):
        pipeline_infrastructure_block = CreatePipeline(config, pipeline_definition)
        return pipeline_infrastructure_block

    @pytest.mark.usefixtures("pipeline_infrastructure_block")
    @pytest.fixture
    def lambda_resource_block(self, pipeline_infrastructure_block):
        lambda_resource_block = CreatePipelineLambdaFunction(
            pipeline_infrastructure_block.config,
            pipeline_infrastructure_block.aws_provider,
            pipeline_infrastructure_block.environment,
            pipeline_infrastructure_block.universal_stack_reference,
            "test:lambda:role",
            "test-function",
            "test/function",
        )
        return lambda_resource_block

    @pytest.mark.usefixtures("lambda_resource_block", "config")
    def test_instantiate_create_lambda_resource(self, lambda_resource_block, config):
        assert lambda_resource_block.project == config.project

    @pytest.mark.usefixtures("lambda_resource_block", "config")
    @pulumi.runtime.test
    def test_lambda_security_group_created(self, lambda_resource_block, config):
        def check_security_group_function(args):
            name, vpc_id, egress = args
            assert name == "test-pipelines-test-test-function-sg"
            assert vpc_id == config.vpc_id
            assert egress == [
                {
                    "from_port": 443,
                    "protocol": "tcp",
                    "to_port": 443,
                    "cidr_blocks": ["0.0.0.0/0"],
                    "description": "HTTPS outbound",
                }
            ]

        security_group = lambda_resource_block.create_lambda_security_group()
        return pulumi.Output.all(
            security_group.name, security_group.vpc_id, security_group.egress
        ).apply(check_security_group_function)

    @pytest.mark.usefixtures("lambda_resource_block", "config")
    @pulumi.runtime.test
    def test_lambda_function_created(self, lambda_resource_block, config):
        def check_lambda_function(args):
            name, role, vpc = args
            assert name == "test-pipelines-test-test-function"
            assert role == "test:lambda:role"
            assert vpc == {
                "security_group_ids": ["test-pipelines-test-test-function-sg"],
                "subnet_ids": config.private_subnet_ids,
            }

        lambda_function = lambda_resource_block.create_lambda(
            aws.ec2.SecurityGroup("test-pipelines-test-test-function-sg"),
            Image(resource_name="test-image", image_name="test-image", skip_push=True),
        )
        return pulumi.Output.all(
            lambda_function.name, lambda_function.role, lambda_function.vpc_config
        ).apply(check_lambda_function)

    @pytest.mark.usefixtures("lambda_resource_block")
    @patch("infrastructure.core._lambda.dirhash")
    @pulumi.runtime.test
    def test_pipeline_creator_apply_docker_image_build_and_push(
        self,
        mock_dirhash: MagicMock,
        lambda_resource_block,
    ):
        def check_built_docker_image(args):
            build, image_name, registry = args
            assert image_name == "test_url:0123abcd"
            assert build == {
                "cacheFrom": {"images": ["test_url:0123abcd"]},
                "args": {
                    "CODE_PATH": "./src/test/function",
                    "BUILDKIT_INLINE_CACHE": "1",
                },
                "builderVersion": "BuilderBuildKit",
                "platform": "linux/amd64",
                "context": "./tests/mock_config_repo_src",
                "dockerfile": "./tests/mock_config_repo_src/src/Dockerfile",
            }
            assert registry == {
                "password": "mock_password",
                "server": "test_url",
                "username": "mock_username",
            }

        mock_dirhash.return_value = "0123abcd"
        mock_registry_info = MockedEcrAuthentication(
            password="mock_password", user_name="mock_username"
        )

        image = lambda_resource_block.apply_docker_image_build_and_push(
            mock_registry_info,
            "test_url",
        )
        return pulumi.Output.all(image.build, image.image_name, image.registry).apply(
            check_built_docker_image
        )

    @pytest.mark.usefixtures("lambda_resource_block")
    def test_lambda_create_apply(
        self,
        lambda_resource_block,
    ):
        function = aws.lambda_.Function(resource_name="lambda", role="abcd")
        security_group = "abc-123"
        registry_info = MockedEcrAuthentication(
            password="mock_password", user_name="mock_username"
        )

        lambda_resource_block.authenticate_to_ecr_repo = Mock(
            return_value=registry_info
        )
        lambda_resource_block.create_lambda_security_group = Mock(
            return_value=security_group
        )
        lambda_resource_block.universal_stack_reference = MagicMock()
        lambda_resource_block.universal_stack_reference.require_output.return_value.apply.return_value = (
            "image"
        )
        lambda_resource_block.create_lambda = MagicMock(return_value=function)

        expected = lambda_resource_block.Output(
            lambda_function=function, name="function"
        )

        res = lambda_resource_block.apply()

        assert res == expected
        lambda_resource_block.authenticate_to_ecr_repo.assert_called_once()
        lambda_resource_block.create_lambda_security_group.assert_called_once()
        lambda_resource_block.create_lambda.assert_called_once_with(
            security_group, "image"
        )
