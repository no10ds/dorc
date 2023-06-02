import pulumi
import pytest
import mock
import os
import json

from utils.config import UniversalConfig, Config
from infrastructure.core.models.definition import (
    PipelineDefinition,
    CloudwatchCronTrigger,
)

from pulumi.runtime.mocks import MockCallArgs, MockResourceArgs
from typing import List, Tuple


class PulumiMocks(pulumi.runtime.Mocks):
    def new_resource(self, args: MockResourceArgs):
        return args.name, args.inputs

    def call(self, args: MockCallArgs) -> Tuple[dict, List[Tuple[str, str]] | None]:
        return {}


@pytest.fixture
def mock_pulumi():
    return pulumi.runtime.set_mocks(PulumiMocks(), preview=False)


@pytest.fixture
def mock_pulumi_config():
    pulumi_config = {"project:environment": "test"}
    with mock.patch.dict(os.environ, dict(PULUMI_CONFIG=json.dumps(pulumi_config))):
        yield


@pytest.fixture
def universal_config() -> UniversalConfig:
    return UniversalConfig(
        region="eu-west-2",
        project="test-pipelines",
        config_repo_path="./tests/mock_config_repo_src",
        tags={"tag": "test"},
    )


@pytest.mark.usefixtures("universal_config")
@pytest.fixture
def config(universal_config) -> Config:
    return Config(
        universal=universal_config,
        vpc_id="test-vpc",
        private_subnet_ids=["test-subnet-1", "test-subnet-2"],
    )


@pytest.fixture
def pipeline_definition() -> PipelineDefinition:
    return PipelineDefinition(
        file_path="tests/mock_config_repo_src/src/layer/test/__main__.py",
        description="Test pipeline description",
        functions=[],
        cloudwatch_trigger=CloudwatchCronTrigger(
            name="test-pipeline-cron", cron="cron(0/6 * * * ? *)"
        ),
    )
