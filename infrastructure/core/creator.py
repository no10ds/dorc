import glob
import os
import re

import pulumi
from pulumi_aws.lambda_ import Function
from pydantic import ValidationError

from infrastructure.core.event_bridge import (
    CreateEventBridgeRule,
    CreateEventBridgeTarget,
)
from infrastructure.core._lambda import CreatePipelineLambdaFunction
from infrastructure.core.state_machine import CreatePipelineStateMachine
from infrastructure.core.models.definition import PipelineDefinition
from utils.abstracts import CreateInfrastructureBlock
from utils.config import Config
from utils.constants import (
    LAMBDA_ROLE_ARN,
    LAMBDA_HANDLER_FILE,
    STATE_FUNCTION_ROLE_ARN,
    CLOUDEVENT_STATE_MACHINE_TRIGGER_ROLE_ARN,
)
from utils.exceptions import InvalidPipelineDefinitionException
from utils.filesystem import extract_lambda_name_from_filepath, path_to_name


class CreatePipeline(CreateInfrastructureBlock):
    def __init__(
        self, config: Config, pipeline_definition: dict | PipelineDefinition
    ) -> None:
        super().__init__(config)

        try:
            if isinstance(pipeline_definition, dict):
                self.pipeline_definition = PipelineDefinition.parse_obj(
                    pipeline_definition
                )
            else:
                self.pipeline_definition = pipeline_definition
        except ValidationError as exception:
            raise InvalidPipelineDefinitionException(str(exception))

        universal_stack_name = os.getenv("UNIVERSAL_STACK_NAME", "universal")
        infra_stack_name = (
            f"{os.getenv('INFRA_STACK_NAME', 'infra')}-{self.environment}"
        )

        self.universal_stack_reference = pulumi.StackReference(universal_stack_name)
        self.infra_stack_reference = pulumi.StackReference(infra_stack_name)

        self.lambda_role_arn = self.infra_stack_reference.require_output(
            LAMBDA_ROLE_ARN
        )

        self.lambda_role_arn = self.get_lambda_role_arn()
        self.state_machine_role_arn = self.get_state_machine_role_arn()
        self.cloudevent_trigger_role_arn = self.get_cloudevent_trigger_role_arn()

        self.pipeline_name = self.generate_pipeline_name_from_directory()

        self.created_lambdas = {}

        # Create infrastructure resource block creators
        self.cloudevent_bridge_rule = CreateEventBridgeRule(
            self.config,
            self.aws_provider,
            self.environment,
            self.pipeline_definition.cloudwatch_trigger,
        )

    def get_lambda_role_arn(self):
        return self.infra_stack_reference.require_output(LAMBDA_ROLE_ARN)

    def get_state_machine_role_arn(self):
        return self.infra_stack_reference.require_output(STATE_FUNCTION_ROLE_ARN)

    def get_cloudevent_trigger_role_arn(self):
        return self.infra_stack_reference.require_output(
            CLOUDEVENT_STATE_MACHINE_TRIGGER_ROLE_ARN
        )

    def fetch_source_directory_name(self):
        top_dir = os.path.dirname(self.pipeline_definition.file_path)
        return os.path.abspath(os.path.join(top_dir, self.config.source_code_folder))

    def apply(self):
        lambda_paths = self.lambda_function_paths()
        lambda_paths.apply(
            lambda names: [self.apply_lambda_function(name).apply() for name in names]
        ).apply(
            lambda outputs: {
                output.name: output.lambda_function.arn for output in outputs
            }
        ).apply(
            lambda lambda_map: self.apply_state_machine(lambda_map).apply()
        ).apply(
            lambda state_machine_outputs: self.apply_cloudwatch_state_machine_trigger(
                state_machine_outputs
            )
            if self.pipeline_definition.cloudwatch_trigger is not None
            else None
        )

    def fetch_lambda_paths(self):
        initial = self.pipeline_definition.file_path.strip("__main__.py")
        path_to_search = os.path.join(initial, "*", LAMBDA_HANDLER_FILE)
        return [
            path.split(f"/{self.config.source_code_folder}/")[-1]
            for path in glob.glob(path_to_search)
        ]

    def lambda_function_paths(self):
        return pulumi.Output.from_input(
            [lambda_path for lambda_path in self.fetch_lambda_paths()]
        )

    def apply_lambda_function(self, lambda_path: str) -> CreatePipelineLambdaFunction:
        return CreatePipelineLambdaFunction(
            config=self.config,
            aws_provider=self.aws_provider,
            environment=self.environment,
            universal_stack_reference=self.universal_stack_reference,
            lambda_role=self.lambda_role_arn,
            function_name=extract_lambda_name_from_filepath(lambda_path),
            code_path=os.path.dirname(lambda_path),
        )

    def apply_state_machine(self, lambdas: list[Function]):
        return CreatePipelineStateMachine(
            self.config,
            self.aws_provider,
            self.environment,
            self.pipeline_name,
            self.pipeline_definition,
            lambdas,
            self.state_machine_role_arn,
        )

    def apply_cloudwatch_state_machine_trigger(
        self, state_machine_outputs: CreatePipelineStateMachine.Output
    ):
        self.cloudevent_bridge_rule.exec()
        cloudevent_bridge_target = CreateEventBridgeTarget(
            self.config,
            self.aws_provider,
            self.environment,
            self.pipeline_name,
            self.pipeline_definition,
            self.cloudevent_bridge_rule.outputs.cloudwatch_event_rule.name,
            self.cloudevent_trigger_role_arn,
            state_machine_outputs.state_machine.arn,
        )
        cloudevent_bridge_target.exec()

    # TODO: Test this
    def generate_pipeline_name_from_directory(self):
        path = self.pipeline_definition.file_path
        matcher = f"{self.config.config_repo_path}/src"
        return path_to_name(re.split(matcher, path)[-1].replace("/__main__.py", ""))
