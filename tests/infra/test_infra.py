import pytest

from mock import Mock
from infrastructure.infra import CreateInfra
from utils.exceptions import EnvironmentRequiredException


class TestCreateInfra:
    @pytest.mark.usefixtures("mock_pulumi", "mock_pulumi_config", "config")
    def test_create_infra(self, mock_pulumi, mock_pulumi_config, config):
        infra_block = CreateInfra(config)
        assert infra_block.config == config
        assert infra_block.environment == "test"

    @pytest.mark.usefixtures("mock_pulumi", "config")
    def test_create_infra_exception_without_environment(self, mock_pulumi, config):
        with pytest.raises(EnvironmentRequiredException) as e_info:
            CreateInfra(config)

        assert (
            str(e_info.value) == "You need to set an environment in the Pulumi config"
        )

    @pytest.mark.usefixtures("mock_pulumi", "mock_pulumi_config", "config")
    def test_create_infra_apply(self, mock_pulumi, mock_pulumi_config, config):
        infra_block = CreateInfra(config)
        mocked_create_iam_resource = Mock()
        infra_block.create_iam_resource = mocked_create_iam_resource
        infra_block.apply()
        mocked_create_iam_resource.exec.assert_called_once()
        mocked_create_iam_resource.export.assert_called_once()
