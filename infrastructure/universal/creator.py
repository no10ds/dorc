from pydantic import ValidationError
from pulumi import Output, ResourceOptions
import pulumi
import pulumi_aws as aws

from utils.tagging import register_default_tags
from utils.exceptions import InvalidConfigException
from utils.provider import create_aws_provider
from infrastructure.universal.config import Config
from infrastructure.universal.iam import CreateIAM


class CreateUniversalPipelineInfrastructure:
    def __init__(self, config: dict | Config) -> None:
        try:
            if isinstance(config, dict):
                self.config = Config.parse_obj(config)
            else:
                self.config = config
        except ValidationError as e:
            # TODO: Probably want a custom error here
            raise InvalidConfigException(str(e))

        register_default_tags(self.config.tags)
        self.aws_provider = create_aws_provider(self.config.region)

    def apply(self) -> None:
        aws.cloudwatch.LogGroup(
            f"{self.config.project}-pipelines-log-group",
            name=f"{self.config.project}-pipelines-log-group",
            opts=ResourceOptions(
                provider=self.aws_provider, delete_before_replace=True
            ),
        )

        CreateIAM(self.aws_provider, self.config).apply()

        self.export()

    def export(self) -> None:
        config_export: dict = dict(self.config)
        for key, value in config_export.items():
            pulumi.export(key, value)
