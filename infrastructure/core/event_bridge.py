import json
import pulumi_aws as aws

from infrastructure.core.models.event_bridge import EventBridge, S3EventBridgeModel
from utils.abstracts import InfrastructureCreateBlock


# TOOD: Probably want this as EventBridgeRule?
class CreateEventBridge(InfrastructureCreateBlock):
    # TODO: Move these parameters into a model - this will need to handle other event types
    def __init__(
        self, event_bridge_name: str, bucket_name: str, key_prefix: str
    ) -> None:
        self.event_bridge_name = event_bridge_name

        self.event_bridge_model = EventBridge(
            model=S3EventBridgeModel(bucket_name=bucket_name, key_prefix=key_prefix)
        )

    def apply(self):
        self.event_bridge = aws.cloudwatch.EventRule(
            resource_name=self.event_bridge_name,
            event_pattern=json.dumps(
                self.event_bridge_model.return_event_bridge_pattern()
            ),
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
