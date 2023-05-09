import pulumi_aws as aws

from infrastructure.core.models.config import CloudwatchCronTrigger, CloudwatchS3Trigger
from utils.abstracts import InfrastructureCreateBlock


class CreateEventBridgeRule(InfrastructureCreateBlock):
    def __init__(self, cloudwatch_trigger: CloudwatchS3Trigger | CloudwatchCronTrigger):
        self.cloudwatch_trigger = cloudwatch_trigger

    def apply(self):
        self.event_bridge = aws.cloudwatch.EventRule(
            resource_name=self.cloudwatch_trigger.name,
            event_pattern=self.cloudwatch_trigger.event_pattern(),
            schedule_expression=self.cloudwatch_trigger.schedule_expression(),
        )

    def get_event_bridge_arn(self):
        return self.event_bridge.arn

    def get_event_bridge_name(self):
        return self.event_bridge.name


class CreateEventBridgeTarget(InfrastructureCreateBlock):
    def __init__(
        self,
        universal_stack_reference,
        event_bridge_target_name: str,
        event_bridge_rule_name: str,
        state_machine_arn,
    ) -> None:
        self.event_bridge_target_name = event_bridge_target_name
        self.event_bridge_rule_name = event_bridge_rule_name
        self.state_machine_arn = state_machine_arn
        self.universal_stack_reference = universal_stack_reference

    def apply(self):
        cloudevent_trigger_arn = self.universal_stack_reference.get_output(
            "cloudevent_state_machine_trigger_role_arn"
        )

        aws.cloudwatch.EventTarget(
            resource_name=self.event_bridge_target_name,
            rule=self.event_bridge_rule_name,
            arn=self.state_machine_arn,
            role_arn=cloudevent_trigger_arn,
        )
