from pulumi import ResourceOptions
from pulumi_aws import Provider
from pulumi_aws.cognito import UserPoolClient

from infrastructure.providers.rapid_client import RapidClient
from infrastructure.core.models.definition import PipelineDefinition, rAPIdTrigger
from utils.abstracts import CreateResourceBlock
from utils.config import Config


class CreateRapidClient(CreateResourceBlock):
    class Output(CreateResourceBlock.Output):
        client: UserPoolClient | RapidClient

    def __init__(
        self,
        config: Config,
        aws_provider: Provider,
        environment: str,
        trigger: rAPIdTrigger,
    ):
        super().__init__(config, aws_provider, environment)
        self.trigger = trigger
        self.project = self.config.project

    def fetch_secret(self) -> Output:
        user_pool = self.get_client_from_user_pool(self.trigger.client_key)
        return self.Output(client=user_pool)

    def apply(self, pipeline_name: str, layer: str, permissions: list[str]) -> Output:
        dorc_client = self.get_client_from_user_pool(
            self.config.rAPId_config.dorc_rapid_client_id
        )
        client_name = f"{self.config.universal.project}_{self.environment}_{layer}_{pipeline_name}"
        return self.Output(
            client=RapidClient(
                client_name,
                dorc_client_id=dorc_client.id,
                dorc_client_secret=dorc_client.client_secret,
                rapid_url=self.config.rAPId_config.url,
                client_name=client_name,
                permissions=permissions,
                opts=ResourceOptions(provider=self.aws_provider),
            )
        )

    def get_client_from_user_pool(self, id: str) -> UserPoolClient:
        return UserPoolClient.get(
            resource_name=f"{self.project}-{self.environment}-{id}",
            id=id,
            user_pool_id=self.config.rAPId_config.user_pool_id,
            opts=ResourceOptions(provider=self.aws_provider),
        )

    def export(self):
        pass


def create_rapid_permissions(
    config: Config, pipeline_definition: PipelineDefinition, layer_folder: str
) -> list[str]:
    domain = pipeline_definition.trigger.domain
    rapid_layer_config = config.universal.get_rapid_layer_config_from_folder(
        layer_folder
    )
    actions = ["READ", "WRITE"]
    layers = [rapid_layer_config.source, rapid_layer_config.target]
    permissions = ["PRIVATE", f"PROTECTED_{domain}"]
    return [
        f"{action}_{layer.upper()}_{permission.upper()}"
        for action in actions
        for layer in layers
        for permission in permissions
    ]
