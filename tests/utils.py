from utils.config import UniversalConfig, Config

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
