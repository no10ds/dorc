import pulumi_aws as aws

from pulumi import ResourceOptions
from pulumi_aws import Provider

from infrastructure.core.models.definition import (
    CloudwatchCronTrigger,
    CloudwatchS3Trigger,
    PipelineDefinition,
)
from utils.abstracts import ResourceCreateBlock
from utils.config import Config


class CreateEventBridgeRule(ResourceCreateBlock):
    def __init__(
        self,
        config: Config,
        aws_provider: Provider,
        environment: str | None,
        cloudwatch_trigger: CloudwatchS3Trigger | CloudwatchCronTrigger,
    ) -> None:
        super().__init__(config, aws_provider, environment)
        self.cloudwatch_trigger = cloudwatch_trigger
        self.project = self.config.project

    def apply(self):
        name = f"{self.project}-{self.environment}-{self.cloudwatch_trigger.name}"
        return aws.cloudwatch.EventRule(
            resource_name=name,
            name=name,
            event_pattern=self.cloudwatch_trigger.event_pattern(),
            schedule_expression=self.cloudwatch_trigger.schedule_expression(),
            opts=ResourceOptions(provider=self.aws_provider),
        )


class CreateEventBridgeTarget(ResourceCreateBlock):
    def __init__(
        self,
        config: Config,
        aws_provider: Provider,
        environment: str | None,
        pipeline_name: str,
        pipeline_definition: PipelineDefinition,
        event_bridge_rule_name: str,
        state_machine,
        cloudevent_trigger_role_arn,
    ) -> None:
        super().__init__(config, aws_provider, environment)
        self.pipeline_name = pipeline_name
        self.pipeline_definition = pipeline_definition
        self.event_bridge_rule_name = event_bridge_rule_name
        self.state_machine = state_machine
        self.cloudevent_trigger_role_arn = cloudevent_trigger_role_arn
        self.project = self.config.project

    def apply(self):
        name = f"{self.project}-{self.environment}-{self.pipeline_name}-target"
        return aws.cloudwatch.EventTarget(
            resource_name=name,
            rule=self.event_bridge_rule_name,
            arn=self.state_machine.arn,
            role_arn=self.cloudevent_trigger_role_arn,
            opts=ResourceOptions(
                provider=self.aws_provider, depends_on=[self.state_machine]
            ),
        )
