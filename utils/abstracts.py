import os
import pulumi

from abc import ABC, abstractmethod
from pydantic import BaseModel  # pylint: disable=no-name-in-module
from pulumi_aws import Provider

from utils.exceptions import EnvironmentRequiredException
from utils.config import Config, UniversalConfig
from utils.tagging import register_default_tags
from utils.provider import create_aws_provider


class CreateInfrastructureBlock(ABC):
    def __init__(
        self, config: Config | UniversalConfig, skip_environment_check: bool = False
    ) -> None:
        super().__init__()
        self.pulumi_config = pulumi.Config()
        self.config = config
        self.config_repo_path = os.getenv("CONFIG_REPO_PATH")
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


class CreateResourceBlock(ABC):
    class Output(BaseModel):
        class Config:
            arbitrary_types_allowed = True

    def __init__(
        self,
        config: Config | UniversalConfig,
        aws_provider: Provider,
        environment: str | None = None,
    ):
        super().__init__()
        self.config = config
        self.aws_provider = aws_provider
        self.environment = environment
        self._outputs: self.Output = None

    @abstractmethod
    def apply(self):
        # Creates the infrastructure and sets the Output
        pass

    @abstractmethod
    def export(self):
        # Export the outputs to Pulumi
        pass

    @property
    def outputs(self) -> Output:
        # Return the output from this pipeline
        if not self._outputs:
            self.exec()

        return self._outputs

    @outputs.setter
    def outputs(self, outputs: Output):
        if not isinstance(outputs, self.Output):
            raise ValueError("Not a valid Outputs instance")
        self._outputs = outputs

    def exec(self):
        self.outputs = self.apply()
