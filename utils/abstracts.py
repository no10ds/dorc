import pulumi

from abc import ABC, abstractmethod
from pulumi_aws import Provider

from utils.exceptions import EnvironmentRequiredException
from utils.config import Config, UniversalConfig
from utils.tagging import register_default_tags
from utils.provider import create_aws_provider


class InfrastructureCreateBlock(ABC):
    def __init__(
        self, config: Config | UniversalConfig, skip_environment_check: bool = False
    ) -> None:
        super().__init__()
        self.pulumi_config = pulumi.Config()
        self.config = config
        register_default_tags(self.config.tags)
        self.aws_provider = create_aws_provider(self.config.region)

        if skip_environment_check is False:
            self.environment = self.pulumi_config.get("environment")
            if self.environment is None:
                raise EnvironmentRequiredException(
                    "You need to set an environment in the Pulumi config"
                )

    @abstractmethod
    def apply(self):
        pass


class ResourceCreateBlock(ABC):
    def __init__(
        self,
        config: Config | UniversalConfig,
        aws_provider: Provider,
        environment: str
        | None = None,  # TODO: Is passing the environment here the best option?
    ) -> None:
        super().__init__()
        self.config = config
        self.aws_provider = aws_provider
        self.environment = environment

    @abstractmethod
    def apply(self):
        pass
