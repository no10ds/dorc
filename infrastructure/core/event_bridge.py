import json
import pulumi
import pulumi_aws as aws

from infrastructure.core.models.event_bridge import EventBridge, S3EventBridgeModel

# TODO: Probably want this to extend a abstract pipeline create class?
class CreateEventBridge():

    # TODO: Move these parameters into a model - this will need to handle other event types
    def __init__(self, event_bridge_name: str, bucket_name: str, key_prefix: str) -> None:
        self.event_bridge_name = event_bridge_name
        
        self.event_bridge_model = EventBridge(
            model=S3EventBridgeModel(
                bucket_name=bucket_name,
                key_prefix=key_prefix
            )
        )

    def apply(self):
        return aws.cloudwatch.EventRule(
            resource_name=self.event_bridge_name,
            event_pattern=json.dumps(self.event_bridge_model.return_event_bridge_pattern())
        )