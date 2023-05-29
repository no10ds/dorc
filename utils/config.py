from typing import Optional
from pydantic import BaseModel  # pylint: disable=no-name-in-module
from pulumi import Output


class UniversalConfig(BaseModel):
    region: str
    project: str
    config_repo_path: str
    tags: Optional[dict] = dict()
    source_code_path: Optional[str] = "src"


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
