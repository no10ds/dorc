from pulumi_aws import Provider
from pulumi_aws.cognito import UserPoolClient

from infrastructure.core.models.definition import rAPIdTrigger
from utils.abstracts import CreateResourceBlock
from utils.config import Config


class CreateRapidClient(CreateResourceBlock):
    class Output(CreateResourceBlock.Output):
        user_pool_client: UserPoolClient

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
        name = f"{self.project}-{self.environment}-static-client"
        user_pool = UserPoolClient.get(
            resource_name=name,
            id=self.trigger.client_key,
            user_pool_id=self.config.rAPId_config.user_pool_id,
        )
        return self.Output(user_pool_client=user_pool)

    def apply(self) -> Output:
        name = f"{self.project}-{self.environment}-client"
        user_pool = UserPoolClient(
            resource_name=name,
            name=name,
            user_pool_id=self.config.rAPId_config.user_pool_id,
            generate_secret=True,
        )
        return self.Output(user_pool_client=user_pool)

    def export(self):
        pass
