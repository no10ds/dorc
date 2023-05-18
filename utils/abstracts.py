from abc import ABC, abstractmethod
from pulumi_aws import Provider

from utils.config import Config, UniversalConfig
from utils.tagging import register_default_tags
from utils.provider import create_aws_provider


class InfrastructureCreateBlock(ABC):
    def __init__(self, config: Config | UniversalConfig) -> None:
        super().__init__()
        self.config = config
        register_default_tags(self.config.tags)
        self.aws_provider = create_aws_provider(self.config.region)

    @abstractmethod
    def apply(self):
        pass


class ResourceCreateBlock(ABC):
    def __init__(
        self, config: Config | UniversalConfig, aws_provider: Provider
    ) -> None:
        super().__init__()
        self.config = config
        self.aws_provider = aws_provider

    @abstractmethod
    def apply(self):
        pass
