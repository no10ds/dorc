import pulumi_aws as aws

from pulumi import ResourceOptions
from pulumi_aws import Provider
from pulumi_aws.cloudwatch import EventRule, EventTarget

from infrastructure.core.models.definition import (
    CronTrigger,
    S3Trigger,
    rAPIdTrigger,
    PipelineDefinition,
)
from utils.abstracts import CreateResourceBlock
from utils.config import Config


class CreateEventBridgeRule(CreateResourceBlock):
    class Output(CreateResourceBlock.Output):
        cloudwatch_event_rule: EventRule

    def __init__(
        self,
        config: Config,
        aws_provider: Provider,
        environment: str,
        trigger: S3Trigger | CronTrigger | rAPIdTrigger,
    ) -> None:
        super().__init__(config, aws_provider, environment)
        self.trigger = trigger
        self.project = self.config.project

    def apply(self) -> Output:
        name = f"{self.project}-{self.environment}-{self.trigger.name}"
        cloudwatch_event_rule = aws.cloudwatch.EventRule(
            resource_name=name,
            name=name,
            event_pattern=self.trigger.event_pattern(""),
            schedule_expression=self.trigger.schedule_expression(),
            opts=ResourceOptions(provider=self.aws_provider),
        )
        output = self.Output(cloudwatch_event_rule=cloudwatch_event_rule)
        return output

    def export(self):
        pass


class CreateEventBridgeTarget(CreateResourceBlock):
    class Output(CreateResourceBlock.Output):
        cloudwatch_event_target: EventTarget

    def __init__(
        self,
        config: Config,
        aws_provider: Provider,
        environment: str,
        pipeline_name: str,
        pipeline_definition: PipelineDefinition,
        event_bridge_rule_name: str,
        cloudevent_trigger_role_arn,
        state_machine_arn,
    ) -> None:
        super().__init__(config, aws_provider, environment)
        self.pipeline_name = pipeline_name
        self.pipeline_definition = pipeline_definition
        self.event_bridge_rule_name = event_bridge_rule_name
        self.state_machine_arn = state_machine_arn
        self.cloudevent_trigger_role_arn = cloudevent_trigger_role_arn
        self.project = self.config.project

    def apply(self) -> Output:
        name = f"{self.project}-{self.environment}-{self.pipeline_name}-target"
        cloudwatch_event_target = aws.cloudwatch.EventTarget(
            resource_name=name,
            rule=self.event_bridge_rule_name,
            arn=self.state_machine_arn,
            role_arn=self.cloudevent_trigger_role_arn,
            opts=ResourceOptions(provider=self.aws_provider),
        )
        output = self.Output(cloudwatch_event_target=cloudwatch_event_target)
        return output

    def export(self):
        pass
