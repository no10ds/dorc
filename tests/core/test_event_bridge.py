import json
import pytest
import pulumi

from infrastructure.core.event_bridge import (
    CreateEventBridgeRule,
    CreateEventBridgeTarget,
)
from infrastructure.core.models.definition import (
    S3Trigger,
    PipelineDefinition,
    rAPIdTrigger,
)
from infrastructure.core.creator import CreatePipeline
from utils.config import Config


class TestCreateEventBridgeRule:
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
    def event_bridge_rule_resource_block(
        self, pipeline_infrastructure_block: CreatePipeline
    ) -> CreateEventBridgeRule:
        event_bridge_rule_resource_block = CreateEventBridgeRule(
            pipeline_infrastructure_block.config,
            pipeline_infrastructure_block.aws_provider,
            pipeline_infrastructure_block.environment,
            pipeline_infrastructure_block.pipeline_definition.trigger,
        )
        return event_bridge_rule_resource_block

    @pytest.mark.usefixtures("event_bridge_rule_resource_block", "config")
    def test_instantiate_create_event_bridge_rule_resource(
        self, event_bridge_rule_resource_block, config
    ):
        assert event_bridge_rule_resource_block.project == config.project

    @pytest.mark.usefixtures("pipeline_infrastructure_block")
    def test_create_event_bridge_with_rapid_trigger(
        self, pipeline_infrastructure_block: CreatePipeline
    ):
        pipeline_infrastructure_block.pipeline_definition.trigger = rAPIdTrigger(
            domain="domain", name="name", client_key="client_key"
        )
        event_bridge_rule_resource_block = CreateEventBridgeRule(
            pipeline_infrastructure_block.config,
            pipeline_infrastructure_block.aws_provider,
            pipeline_infrastructure_block.environment,
            pipeline_infrastructure_block.pipeline_definition.trigger,
        )
        assert event_bridge_rule_resource_block.is_rapid_trigger is True

    @pytest.mark.usefixtures("event_bridge_rule_resource_block")
    @pulumi.runtime.test
    def test_event_bridge_cron_rule_created(
        self, event_bridge_rule_resource_block: CreateEventBridgeRule
    ):
        def check_event_bridge_rule(args):
            name, event_pattern, schedule_expression = args
            assert name == "test-pipelines-test-test-pipeline-cron"
            assert event_pattern is None
            assert schedule_expression == "cron(0/6 * * * ? *)"

        event_bridge_rule = (
            event_bridge_rule_resource_block.outputs.cloudwatch_event_rule
        )
        return pulumi.Output.all(
            event_bridge_rule.name,
            event_bridge_rule.event_pattern,
            event_bridge_rule.schedule_expression,
        ).apply(check_event_bridge_rule)

    @pytest.mark.usefixtures("event_bridge_rule_resource_block")
    @pulumi.runtime.test
    def test_event_bridge_s3_rule_created(
        self, event_bridge_rule_resource_block: CreateEventBridgeRule
    ):
        def check_event_bridge_rule(args):
            name, event_pattern, schedule_expression = args
            assert name == "test-pipelines-test-test-trigger"
            assert event_pattern == json.dumps(
                {
                    "source": ["aws.s3"],
                    "detail": {
                        "eventSource": ["s3.amazonaws.com"],
                        "eventName": ["PutObject", "CompleteMultipartUpload"],
                        "requestParameters": {
                            "bucketName": ["test-bucket"],
                            "key": [{"prefix": "test-key"}],
                        },
                    },
                }
            )
            assert schedule_expression is None

        event_bridge_rule_resource_block.trigger = S3Trigger(
            name="test-trigger", bucket_name="test-bucket", key_prefix="test-key"
        )
        event_bridge_rule = (
            event_bridge_rule_resource_block.outputs.cloudwatch_event_rule
        )
        return pulumi.Output.all(
            event_bridge_rule.name,
            event_bridge_rule.event_pattern,
            event_bridge_rule.schedule_expression,
        ).apply(check_event_bridge_rule)


class TestCreateEventBridgeTarget:
    @pytest.mark.usefixtures(
        "mock_pulumi", "mock_pulumi_config", "config", "pipeline_definition"
    )
    @pytest.fixture
    def pipeline_infrastructure_block(
        self, mock_pulumi, mock_pulumi_config, config, pipeline_definition
    ):
        pipeline_infrastructure_block = CreatePipeline(config, pipeline_definition)
        return pipeline_infrastructure_block

    @pytest.mark.usefixtures("pipelines_infrastructure_block")
    @pytest.fixture
    def event_bridge_target_resource_block(
        self, pipeline_infrastructure_block: CreatePipeline
    ) -> CreateEventBridgeTarget:
        event_bridge_target_resource_block = CreateEventBridgeTarget(
            pipeline_infrastructure_block.config,
            pipeline_infrastructure_block.aws_provider,
            pipeline_infrastructure_block.environment,
            "test-pipeline",
            pipeline_infrastructure_block.pipeline_definition.trigger,
            "test-event-bridge-rule",
            "test:cloudwatch:role:arn",
            "test:state:machine:arn",
        )
        return event_bridge_target_resource_block

    @pytest.mark.usefixtures("event_bridge_target_resource_block", "config")
    def test_instantiate_create_event_bridge_target_resource(
        self, event_bridge_target_resource_block, config
    ):
        assert event_bridge_target_resource_block.project == config.project

    @pytest.mark.usefixtures("event_bridge_target_resource_block")
    @pulumi.runtime.test
    def test_event_bridge_target_created(
        self, event_bridge_target_resource_block: CreateEventBridgeTarget
    ):
        def check_event_bridge_target(args):
            rule, arn, role_arn = args
            assert rule == "test-event-bridge-rule"
            assert arn == "test:state:machine:arn"
            assert role_arn == "test:cloudwatch:role:arn"

        event_bridge_target = (
            event_bridge_target_resource_block.outputs.cloudwatch_event_target
        )
        return pulumi.Output.all(
            event_bridge_target.rule,
            event_bridge_target.arn,
            event_bridge_target.role_arn,
        ).apply(check_event_bridge_target)
