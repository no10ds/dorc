import pulumi
import pulumi_aws as aws
from pulumi import ResourceOptions
from pulumi_aws import Provider
from pulumi_aws.ecr import Repository

from utils.abstracts import CreateResourceBlock
from utils.config import UniversalConfig


class CreateEcrResource(CreateResourceBlock):
    class Output(CreateResourceBlock.Output):
        ecr_repo: Repository

    def __init__(self, config: UniversalConfig, aws_provider: Provider, repo_name: str):
        super().__init__(config, aws_provider)
        self.repo_name = repo_name

    def apply(self) -> Output:
        name = f"{self.config.project}-{self.repo_name}"
        ecr_repo = aws.ecr.Repository(
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
        output = self.Output(ecr_repo=ecr_repo)
        return output

    def export(self):
        pulumi.export(f"ecr_repository_{self.repo_name}_arn", self.outputs.ecr_repo.arn)
        pulumi.export(
            f"ecr_repository_{self.repo_name}_id", self.outputs.ecr_repo.registry_id
        )
        pulumi.export(
            f"ecr_repository_{self.repo_name}_url", self.outputs.ecr_repo.repository_url
        )
