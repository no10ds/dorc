import json

from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, validator  # pylint: disable=no-name-in-module

from infrastructure.core.models.event_bridge import EventBridge, S3EventBridgeModel


class rAPIdTrigger(BaseModel):
    domain: str
    name: str
    client_key: Optional[str]

    def create_s3_path_prefix(self, layer: str) -> str:
        return f"data/{layer}/{self.domain.lower()}/{self.name}/"

    def event_pattern(self, layer: str, data_bucket_name: str):
        s3_path_prefix = self.create_s3_path_prefix(layer)
        event_bridge_model = EventBridge(
            model=S3EventBridgeModel(
                bucket_name=data_bucket_name, key_prefix=s3_path_prefix
            )
        )
        return json.dumps(event_bridge_model.return_event_bridge_pattern())

    def schedule_expression(self):
        return None


class S3Trigger(BaseModel):
    name: str
    bucket_name: str
    key_prefix: str

    def event_pattern(self):
        event_bridge_model = EventBridge(
            model=S3EventBridgeModel(
                bucket_name=self.bucket_name, key_prefix=self.key_prefix
            )
        )

        return json.dumps(event_bridge_model.return_event_bridge_pattern())

    def schedule_expression(self):
        return None


class CronTrigger(BaseModel):
    name: str
    cron: str

    def event_pattern(self):
        return None

    def schedule_expression(self):
        return self.cron


class NextFunctionTypes(StrEnum):
    FUNCTION = "Function"
    PIPELINE = "Pipeline"


class NextFunction(BaseModel):
    name: str
    type: Optional[NextFunctionTypes] = NextFunctionTypes.FUNCTION


class Function(BaseModel):
    name: str
    next_function: Optional[str | NextFunction] = None


class PipelineDefinition(BaseModel):
    file_path: str
    description: Optional[str] = ""
    functions: list[Function]
    trigger: Optional[S3Trigger | CronTrigger | rAPIdTrigger] = None

    @validator("functions")
    def check_for_only_one_termination(
        cls, functions: list[Function]
    ):  # pylint: disable=no-self-argument
        termination_steps = sum(
            1 for function in functions if function.next_function is None
        )
        if termination_steps > 1:
            raise ValueError(
                "Pipeline definition can only contain one termination step"
            )
        return functions
