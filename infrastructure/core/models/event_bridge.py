from pydantic import BaseModel  # pylint: disable=no-name-in-module


class S3EventBridgeModel(BaseModel):
    bucket_name: str
    key_prefix: str

    def return_event_bridge_pattern(self):
        return {
            "source": ["aws.s3"],
            "detail-type": ["Object Created"],
            "detail": {
                "bucket": {"name": [self.bucket_name]},
                "object": {"key": [{"prefix": self.key_prefix}]},
            },
        }


class EventBridge(BaseModel):
    model: S3EventBridgeModel

    def return_event_bridge_pattern(self):
        return self.model.return_event_bridge_pattern()
