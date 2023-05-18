import json
from enum import StrEnum
from typing import Optional
from pydantic import BaseModel, validator

from infrastructure.core.models.event_bridge import EventBridge, S3EventBridgeModel


class CloudwatchS3Trigger(BaseModel):
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


class CloudwatchCronTrigger(BaseModel):
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
    pipeline_name: str
    functions: list[Function]
    cloudwatch_trigger: Optional[CloudwatchS3Trigger | CloudwatchCronTrigger] = None

    @validator("functions")
    def check_for_only_one_termination(cls, value: list[Function]):
        nones_found = 0
        for function in value:
            if function.next_function is None:
                nones_found += 1
            if nones_found > 1:
                raise ValueError(
                    "Pipeline definition can only contain one termination step"
                )
        return value
