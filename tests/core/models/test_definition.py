import pytest
import json

from infrastructure.core.models.definition import (
    S3Trigger,
    CronTrigger,
)


class TestS3Trigger:
    @pytest.fixture
    def s3_trigger(self) -> S3Trigger:
        return S3Trigger(
            name="test-s3-trigger",
            bucket_name="test-bucket",
            key_prefix="test/prefix",
        )

    @pytest.mark.usefixtures("s3_trigger")
    def test_event_pattern(self, s3_trigger):
        event_pattern = s3_trigger.event_pattern()
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

    @pytest.mark.usefixtures("s3_trigger")
    def test_schedule_expression(self, s3_trigger):
        schedule_expression = s3_trigger.schedule_expression()
        assert schedule_expression is None


class TestCronTrigger:
    @pytest.fixture
    def cron_trigger(self) -> CronTrigger:
        return CronTrigger(name="test-cron-trigger", cron="cron(0/5 * * * ? *)")

    @pytest.mark.usefixtures("cron_trigger")
    def test_event_pattern(self, cron_trigger):
        event_pattern = cron_trigger.event_pattern()
        assert event_pattern is None

    @pytest.mark.usefixtures("cron_trigger")
    def test_schedule_expression(self, cron_trigger):
        schedule_expression = cron_trigger.schedule_expression()
        assert schedule_expression == "cron(0/5 * * * ? *)"
