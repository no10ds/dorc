from infrastructure.infra.iam import CreateIamResource
from utils.abstracts import InfrastructureCreateBlock
from utils.config import Config


class CreateInfra(InfrastructureCreateBlock):
    def __init__(self, config: Config) -> None:
        super().__init__(config)
        self.create_iam_resource = CreateIamResource(
            self.config, self.aws_provider, self.environment
        )

    def apply(self):
        self.create_iam_resource.apply()
