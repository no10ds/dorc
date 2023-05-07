from pydantic import BaseModel

class S3EventBridgeModel(BaseModel):
    bucket_name: str
    key_prefix: str

    def return_s3_pattern_detail(self):
        return {
            "eventSource": ["s3.amazonaws.com"],
            "eventName": ["PutObject", "CompleteMultipartUpload"],
            "requestParameters": {
                "bucketName": [f"{self.bucket_name}"],
                "key": [{
                    "prefix": self.key_prefix
                }]
            }
        }

# TODO: We need to expand this out further to other event bridge types
class EventBridge(BaseModel):
    model: S3EventBridgeModel

    def return_event_bridge_pattern(self):
        return {
            "source": ["aws.s3"],
            "detail": self.model.return_s3_pattern_detail()
        }
