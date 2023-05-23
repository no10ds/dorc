import pytest

from infrastructure.infra import CreateInfra
from utils.exceptions import EnvironmentRequiredException

from tests.utils import config


class TestCreateInfra:
    def test_create_infra(self, mock_pulumi, mock_pulumi_config):
        infra_block = CreateInfra(config)
        assert infra_block.config == config
        assert infra_block.environment == "test"

    def test_create_infra_exception_without_environment(self, mock_pulumi):
        with pytest.raises(EnvironmentRequiredException) as e_info:
            CreateInfra(config)

        assert (
            str(e_info.value) == "You need to set an environment in the Pulumi config"
        )
