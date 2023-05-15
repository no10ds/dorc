from typing import Optional
from pydantic import BaseModel
from pulumi import Output


class Config(BaseModel):
    region: str
    project: str
    config_repo_path: str
    tags: Optional[dict] = dict()
    vpc_id: Output[str] | str
    private_subnet_ids: Output[list[str]] | list[str]

    source_code_path: Optional[str] = "src"
    additional_lambda_role_policy_arn: Optional[Output[str] | str]
    additional_state_function_role_policy_arn: Optional[Output[str] | str]
    additional_cloudevent_state_machine_trigger_role_policy_arn: Optional[
        Output[str] | str
    ]

    class Config:
        arbitrary_types_allowed = True
