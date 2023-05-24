import pytest
import pulumi

from pulumi_docker import Image
from infrastructure.core.lambda_ import CreatePipelineLambdaFunction
from infrastructure.core.creator import CreatePipeline

from tests.utils import config, pipeline_definition


class TestCreateLambda:
    @pytest.mark.usefixtures("mock_pulumi", "mock_pulumi_config")
    @pytest.fixture
    def pipeline_infrastructure_block(self, mock_pulumi, mock_pulumi_config):
        pipeline_infrastructure_block = CreatePipeline(config, pipeline_definition)
        yield pipeline_infrastructure_block

    @pytest.mark.usefixtures("pipeline_infrastructure_block")
    @pytest.fixture
    def lambda_resource_block(self, pipeline_infrastructure_block):
        image = Image(
            resource_name="test-image", image_name="test-image", skip_push=True
        )
        lambda_resource_block = CreatePipelineLambdaFunction(
            pipeline_infrastructure_block.config,
            pipeline_infrastructure_block.aws_provider,
            pipeline_infrastructure_block.environment,
            "test:lambda:role",
            "test-function",
            image,
        )
        yield lambda_resource_block

    @pytest.mark.usefixtures("lambda_resource_block")
    @pulumi.runtime.test
    def test_instantiate_create_lambda_resource(self, lambda_resource_block):
        assert lambda_resource_block.project == config.project

    @pytest.mark.usefixtures("lambda_resource_block")
    @pulumi.runtime.test
    def test_lambda_security_group_created(self, lambda_resource_block):
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

        security_group = lambda_resource_block.outputs.security_group
        return pulumi.Output.all(
            security_group.name, security_group.vpc_id, security_group.egress
        ).apply(check_security_group_function)

    @pytest.mark.usefixtures("lambda_resource_block")
    @pulumi.runtime.test
    def test_lambda_function_created(self, lambda_resource_block):
        def check_lambda_function(args):
            name, role, vpc = args
            assert name == "test-pipelines-test-test-function"
            assert role == "test:lambda:role"
            assert vpc == {
                "security_group_ids": ["test-pipelines-test-test-function-sg_id"],
                "subnet_ids": config.private_subnet_ids,
            }

        lambda_function = lambda_resource_block.outputs.lambda_function
        return pulumi.Output.all(
            lambda_function.name, lambda_function.role, lambda_function.vpc_config
        ).apply(check_lambda_function)
