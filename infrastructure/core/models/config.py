from enum import Enum
from typing import Optional
from pydantic import BaseModel, validator


class CloudwatchTrigger(BaseModel):
    bucket_name: str
    key_prefix: str


class NextPipelineTypes(str, Enum):
    function = "function"
    pipeline = "pipeline"


class NextPipeline(BaseModel):
    name: str
    type: Optional[NextPipelineTypes] = NextPipelineTypes.function

    class Config:
        use_enum_values = True


class Pipeline(BaseModel):
    function_name: str
    next_function: Optional[str | NextPipeline] = None


class Config(BaseModel):
    file_path: str
    pipeline_name: str
    pipelines: list[Pipeline]
    cloudwatch_trigger: Optional[CloudwatchTrigger] = None

    @validator("pipelines")
    def check_for_only_one_termination(cls, value: list[Pipeline]):
        nones_found = 0
        for pipeline in value:
            if pipeline.next_function is None:
                nones_found += 1
            if nones_found > 1:
                raise ValueError(
                    "Pipeline config can only contain one termination step"
                )
        return value
