import pulumi
import pulumi_aws as aws
from typing import Any
from pulumi import Output, ResourceOptions
from pulumi_aws import Provider

from utils.abstracts import InfrastructureCreateBlock


class CreateECRRepo(InfrastructureCreateBlock):
    def __init__(
        self, aws_provider: Provider, project: Output[Any], pipeline_name: str
    ):
        self.aws_provider = aws_provider
        self.project = project
        self.pipline_name = pipeline_name

    def apply(self):
        self.ecr_repo = self.project.apply(
            lambda project: aws.ecr.Repository(
                resource_name=f"{project}-{self.pipline_name}",
                name=f"{project}-{self.pipline_name}",
                image_scanning_configuration=aws.ecr.RepositoryImageScanningConfigurationArgs(
                    scan_on_push=True
                ),
                force_delete=True,
                encryption_configurations=[
                    aws.ecr.RepositoryEncryptionConfigurationArgs(encryption_type="KMS")
                ],
                opts=ResourceOptions(provider=self.aws_provider),
            )
        )

        self.export()

    def export(self):
        pulumi.export(f"ecr_repository_{self.pipline_name}_arn", self.ecr_repo.arn)

    def get_repo_registry_id(self):
        return self.ecr_repo.registry_id

    def get_repo_url(self):
        return self.ecr_repo.repository_url
