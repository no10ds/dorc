from pydantic import BaseModel  # pylint: disable=no-name-in-module

from utils.config import UniversalConfig, Config
from infrastructure.core.models.definition import (
    PipelineDefinition,
    CloudwatchCronTrigger,
)

universal_config = UniversalConfig(
    region="eu-west-2",
    project="test-pipelines",
    config_repo_path="./tests/mock_config_repo_src",
    tags={"tag": "test"},
)

config = Config(
    universal=universal_config,
    vpc_id="test-vpc",
    private_subnet_ids=["test-subnet-1", "test-subnet-2"],
)

pipeline_definition = PipelineDefinition(
    file_path="./tests/mock_config_repo_src/src/test/layer/__main__.py",
    description="Test pipeline description",
    functions=[],
    cloudwatch_trigger=CloudwatchCronTrigger(
        name="test-pipeline-cron", cron="cron(0/6 * * * ? *)"
    ),
)


class MockedEcrAuthentication(BaseModel):
    password: str
    user_name: str
