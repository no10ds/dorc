from mock import MagicMock, Mock, patch, call, ANY
import pytest
import pulumi

from infrastructure.core.rapid_client import CreateRapidClient, create_rapid_permissions
from infrastructure.core.creator import CreatePipeline
from infrastructure.core.models.definition import rAPIdTrigger
from utils.config import rAPIdConfig, LayerConfig


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
            prefix="prefix",
            user_pool_id="xxx-yyy-user-pool",
            dorc_rapid_client_id="dorc-xxx-yyy",
            url="https://rapid.example.com/api",
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

        user_pool_client = rapid_client_resource_block.fetch_secret().client
        return pulumi.Output.all(
            user_pool_client.id, user_pool_client.user_pool_id
        ).apply(check_user_pool_client)

    @pytest.mark.usefixtures("rapid_client_resource_block")
    @pulumi.runtime.test
    def test_rapid_client_apply(self, rapid_client_resource_block):
        def check_user_pool_client(args):
            client_name, permissions = args
            assert client_name == "test-pipelines_test_default_test-pipeline"
            assert permissions == ["READ_PRIVATE"]

        user_pool_client = rapid_client_resource_block.apply(
            pipeline_name="test-pipeline", layer="default", permissions=["READ_PRIVATE"]
        ).client
        return pulumi.Output.all(
            user_pool_client.client_name, user_pool_client.permissions
        ).apply(check_user_pool_client)


class TestCreateRapidPermissions:
    @pytest.mark.usefixtures("config", "pipeline_definition")
    def test_create_rapid_permissions(self, config, pipeline_definition):
        pipeline_definition.trigger = rAPIdTrigger(
            domain="domain", name="name", client_key="client-key"
        )
        config.universal.rapid_layer_config = [
            LayerConfig(folder="layer", source="default1", target="default2")
        ]
        permissions = create_rapid_permissions(config, pipeline_definition, "layer")
        assert permissions == [
            "READ_DEFAULT1_PRIVATE",
            "READ_DEFAULT1_PROTECTED_DOMAIN",
            "READ_DEFAULT2_PRIVATE",
            "READ_DEFAULT2_PROTECTED_DOMAIN",
            "WRITE_DEFAULT1_PRIVATE",
            "WRITE_DEFAULT1_PROTECTED_DOMAIN",
            "WRITE_DEFAULT2_PRIVATE",
            "WRITE_DEFAULT2_PROTECTED_DOMAIN",
        ]
