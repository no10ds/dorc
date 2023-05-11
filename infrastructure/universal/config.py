from typing import Optional
from pydantic import BaseModel
from pulumi import Output


class Config(BaseModel):
    project: str
    config_repo_path: str
    vpc_id: Output | str
    private_subnet_ids: Output | list[str]

    source_code_path: Optional[str] = "src"

    class Config:
        arbitrary_types_allowed = True
