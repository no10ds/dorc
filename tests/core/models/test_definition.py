import pytest
import json

from infrastructure.core.models.definition import (
    CloudwatchS3Trigger,
    CloudwatchCronTrigger,
)


class TestCloudwatchS3Trigger:
    @pytest.fixture
    def cloudwatch_s3_trigger(self) -> CloudwatchS3Trigger:
        return CloudwatchS3Trigger(
            name="test-s3-trigger",
            bucket_name="test-bucket",
            key_prefix="test/prefix",
        )

    @pytest.mark.usefixtures("cloudwatch_s3_trigger")
    def test_event_pattern(self, cloudwatch_s3_trigger):
        event_pattern = cloudwatch_s3_trigger.event_pattern()
        assert event_pattern == json.dumps(
            {
                "source": ["aws.s3"],
                "detail": {
                    "eventSource": ["s3.amazonaws.com"],
                    "eventName": ["PutObject", "CompleteMultipartUpload"],
                    "requestParameters": {
                        "bucketName": ["test-bucket"],
                        "key": [{"prefix": "test/prefix"}],
                    },
                },
            }
        )

    @pytest.mark.usefixtures("cloudwatch_s3_trigger")
    def test_schedule_expression(self, cloudwatch_s3_trigger):
        schedule_expression = cloudwatch_s3_trigger.schedule_expression()
        assert schedule_expression is None


class TestCloudwatchCronTrigger:
    @pytest.fixture
    def cloudwatch_cron_trigger(self) -> CloudwatchCronTrigger:
        return CloudwatchCronTrigger(
            name="test-cron-trigger", cron="cron(0/5 * * * ? *)"
        )

    @pytest.mark.usefixtures("cloudwatch_cron_trigger")
    def test_event_pattern(self, cloudwatch_cron_trigger):
        event_pattern = cloudwatch_cron_trigger.event_pattern()
        assert event_pattern is None

    @pytest.mark.usefixtures("cloudwatch_cron_trigger")
    def test_schedule_expression(self, cloudwatch_cron_trigger):
        schedule_expression = cloudwatch_cron_trigger.schedule_expression()
        assert schedule_expression == "cron(0/5 * * * ? *)"
