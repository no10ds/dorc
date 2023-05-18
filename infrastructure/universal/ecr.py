import pulumi
import pulumi_aws as aws
from pulumi import ResourceOptions
from pulumi_aws import Provider

from utils.abstracts import ResourceCreateBlock
from utils.config import UniversalConfig


class CreateEcrResource(ResourceCreateBlock):
    def __init__(
        self, config: UniversalConfig, aws_provider: Provider, repo_name: str
    ) -> None:
        super().__init__(config, aws_provider)
        self.repo_name = repo_name

    def apply(self):
        name = f"{self.config.project}-{self.repo_name}"
        self.ecr_repo = aws.ecr.Repository(
            resource_name=name,
            name=name,
            image_scanning_configuration=aws.ecr.RepositoryImageScanningConfigurationArgs(
                scan_on_push=True
            ),
            force_delete=True,
            encryption_configurations=[
                aws.ecr.RepositoryEncryptionConfigurationArgs(encryption_type="KMS")
            ],
            opts=ResourceOptions(provider=self.aws_provider),
        )

    def export(self):
        pulumi.export(f"ecr_repository_{self.repo_name}_arn", self.ecr_repo.arn)
        pulumi.export(f"ecr_repository_{self.repo_name}_id", self.ecr_repo.registry_id)
        pulumi.export(
            f"ecr_repository_{self.repo_name}_url", self.ecr_repo.repository_url
        )
