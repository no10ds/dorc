import os
import glob

from infrastructure.universal.ecr import CreateEcrResource
from utils.abstracts import CreateInfrastructureBlock
from utils.config import UniversalConfig


class CreateUniversal(CreateInfrastructureBlock):
    def __init__(self, config: UniversalConfig) -> None:
        super().__init__(config, skip_environment_check=True)
        self.repo_list = self.retrieve_repo_list_from_folders()

    def retrieve_repo_list_from_folders(self) -> list[str]:
        source_path = f"{self.config_repo_path}/{self.config.source_code_folder}"
        return [
            dirpath.replace(source_path, "").strip("/").replace("/", "-")
            for dirpath in glob.glob(os.path.join(source_path, "*", "*"))
            if os.path.isdir(dirpath)
        ]

    def apply(self):
        for repo in self.repo_list:
            create_ecr_resource = CreateEcrResource(
                self.config, self.aws_provider, repo
            )
            create_ecr_resource.exec()
            create_ecr_resource.export()
