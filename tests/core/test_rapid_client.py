from mock import MagicMock, Mock, patch, call, ANY
import pytest
import pulumi

from infrastructure.core.rapid_client import CreateRapidClient
from infrastructure.core.creator import CreatePipeline
from infrastructure.core.models.definition import rAPIdTrigger
from utils.config import rAPIdConfig


class TestCreateRapidClient:
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
    def rapid_client_resource_block(self, pipeline_infrastructure_block):
        pipeline_infrastructure_block.pipeline_definition.trigger = rAPIdTrigger(
            domain="domain", name="name", client_key="client-key"
        )
        pipeline_infrastructure_block.config.rAPId_config = rAPIdConfig(
            prefix="prefix", user_pool_id="xxx-yyy-user-pool"
        )
        rapid_client_resource_block = CreateRapidClient(
            pipeline_infrastructure_block.config,
            pipeline_infrastructure_block.aws_provider,
            pipeline_infrastructure_block.environment,
            pipeline_infrastructure_block.pipeline_definition.trigger,
        )
        return rapid_client_resource_block

    @pytest.mark.usefixtures("rapid_client_resource_block", "config")
    def test_instantiate_create_rapid_client_resource(
        self, rapid_client_resource_block, config
    ):
        assert rapid_client_resource_block.project == config.project

    @pytest.mark.usefixtures("rapid_client_resource_block")
    @pulumi.runtime.test
    def test_rapid_client_fetch_secret(self, rapid_client_resource_block):
        def check_user_pool_client(args):
            _id, user_pool_id = args
            assert _id == "client-key"
            assert user_pool_id == "xxx-yyy-user-pool"

        user_pool_client = rapid_client_resource_block.fetch_secret().user_pool_client
        return pulumi.Output.all(
            user_pool_client.id, user_pool_client.user_pool_id
        ).apply(check_user_pool_client)

    @pytest.mark.usefixtures("rapid_client_resource_block")
    @pulumi.runtime.test
    def test_rapid_client_apply(self, rapid_client_resource_block):
        def check_user_pool_client(args):
            name, user_pool_id, generate_secret = args
            assert name == "test-pipelines-test-client"
            assert user_pool_id == "xxx-yyy-user-pool"
            assert generate_secret is True

        user_pool_client = rapid_client_resource_block.apply().user_pool_client
        return pulumi.Output.all(
            user_pool_client.name,
            user_pool_client.user_pool_id,
            user_pool_client.generate_secret,
        ).apply(check_user_pool_client)
