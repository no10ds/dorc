import pulumi
import pytest
import mock
import os
import json

from pulumi.runtime.mocks import MockCallArgs, MockResourceArgs
from typing import List, Tuple


class PulumiMocks(pulumi.runtime.Mocks):
    def new_resource(self, args: MockResourceArgs):
        return [f"{args.name}_id", args.inputs]

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
