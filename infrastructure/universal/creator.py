import os
from glob import glob

from infrastructure.universal.ecr import CreateEcrResource
from utils.abstracts import CreateInfrastructureBlock
from utils.config import UniversalConfig
from utils.constants import LAMBDA_HANDLER_FILE
from utils.filesystem import extract_lambda_name_from_filepath


class CreateUniversal(CreateInfrastructureBlock):
    def __init__(self, config: UniversalConfig) -> None:
        super().__init__(config, skip_environment_check=True)
        self.repo_list = self.retrieve_repo_list_from_folders()

    def retrieve_repo_list_from_folders(self) -> list[str]:
        return [
            extract_lambda_name_from_filepath(
                path.replace(self.config.source_code_path, "")
            )
            for path in glob(
                os.path.join(
                    self.config.source_code_path, "*", "*", "*", LAMBDA_HANDLER_FILE
                )
            )
        ]

    def apply(self):
        for repo in self.repo_list:
            create_ecr_resource = CreateEcrResource(
                self.config, self.aws_provider, repo
            )
            create_ecr_resource.exec()
            create_ecr_resource.export()
