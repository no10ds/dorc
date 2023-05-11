import pulumi
import pulumi_aws as aws

from utils.abstracts import InfrastructureCreateBlock


class CreateECRRepo(InfrastructureCreateBlock):
    def __init__(self, pipeline_name: str):
        self.pipline_name = pipeline_name

    def apply(self):
        self.ecr_repo = aws.ecr.Repository(
            resource_name=self.pipline_name,
            image_scanning_configuration=aws.ecr.RepositoryImageScanningConfigurationArgs(
                scan_on_push=True
            ),
            encryption_configurations=[
                aws.ecr.RepositoryEncryptionConfigurationArgs(encryption_type="KMS")
            ],
        )

        self.export()

    def export(self):
        pulumi.export(f"ecr_repository_{self.pipline_name}_arn", self.ecr_repo.arn)

    def get_repo_registry_id(self):
        return self.ecr_repo.registry_id

    def get_repo_url(self):
        return self.ecr_repo.repository_url
