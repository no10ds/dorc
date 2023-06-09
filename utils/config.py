import os
from typing import Optional

from pydantic import BaseModel  # pylint: disable=no-name-in-module
from pulumi import Output

from utils.exceptions import (
    CannotFindEnvironmentVariableException,
)


class UniversalConfig(BaseModel):
    region: str
    project: str
    tags: Optional[dict] = dict()
    source_code_folder: Optional[str] = "src"
    config_repo_path: Optional[str] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config_repo_path = self.evaluate_environment_variable_input(
            "CONFIG_REPO_PATH"
        )

    def evaluate_environment_variable_input(self, environment_variable: str):
        value = os.getenv(environment_variable)
        if not value:
            raise CannotFindEnvironmentVariableException(
                f"No environment variable found for {environment_variable}"
            )
        return value

    @property
    def source_code_path(self) -> str:
        return os.path.join(self.config_repo_path, self.source_code_folder)


class Config(BaseModel):
    universal: UniversalConfig
    vpc_id: Output[str] | str
    private_subnet_ids: Output[list[str]] | list[str]

    additional_lambda_role_policy_arn: Optional[Output[str] | str]
    additional_state_function_role_policy_arn: Optional[Output[str] | str]
    additional_cloudevent_state_machine_trigger_role_policy_arn: Optional[
        Output[str] | str
    ]

    class Config:
        arbitrary_types_allowed = True

    def __getattr__(self, name):
        return getattr(self.universal, name)
