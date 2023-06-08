from pydantic import BaseModel  # pylint: disable=no-name-in-module


class S3EventBridgeModel(BaseModel):
    bucket_name: str
    key_prefix: str

    def return_event_bridge_pattern(self):
        return {
            "source": ["aws.s3"],
            "detail": {
                "eventSource": ["s3.amazonaws.com"],
                "eventName": ["PutObject", "CompleteMultipartUpload"],
                "requestParameters": {
                    "bucketName": [f"{self.bucket_name}"],
                    "key": [{"prefix": self.key_prefix}],
                },
            },
        }


class CrawlerEventBridgeModel(BaseModel):
    crawler_name: str

    def return_event_bridge_pattern(self):
        return {
            "source": ["aws.glue"],
            "detail": {"crawlerName": [self.crawler_name], "state": ["Succeeded"]},
        }


class EventBridge(BaseModel):
    model: S3EventBridgeModel | CrawlerEventBridgeModel

    def return_event_bridge_pattern(self):
        return self.model.return_event_bridge_pattern()
