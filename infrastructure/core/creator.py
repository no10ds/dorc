import glob
import os
import re

import pulumi

from pulumi_aws.lambda_ import Function
from pulumi_aws.cognito import UserPoolClient
from pydantic import ValidationError

from infrastructure.core.event_bridge import (
    CreateEventBridgeRule,
    CreateEventBridgeTarget,
)
from infrastructure.core.rapid_client import CreateRapidClient, create_rapid_permissions
from infrastructure.core._lambda import CreatePipelineLambdaFunction
from infrastructure.core.state_machine import CreatePipelineStateMachine
from infrastructure.core.models.definition import PipelineDefinition, rAPIdTrigger
from infrastructure.core.validators import validate_rapid_trigger
from infrastructure.providers.rapid_client import RapidClient
from utils.abstracts import CreateInfrastructureBlock
from utils.config import Config
from utils.constants import (
    LAMBDA_ROLE_ARN,
    LAMBDA_HANDLER_FILE,
    STATE_FUNCTION_ROLE_ARN,
    CLOUDEVENT_STATE_MACHINE_TRIGGER_ROLE_ARN,
)
from utils.exceptions import (
    InvalidPipelineDefinitionException,
)
from utils.filesystem import extract_lambda_name_from_filepath, path_to_name


class FileStructure:
    def __init__(self, lambda_paths: list[str]):
        self.lambda_paths = lambda_paths
        self.layer = self.lambda_paths[0].split("/")[0]
        self.pipeline_name = self.lambda_paths[0].split("/")[1]


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

        self.created_lambdas = {}
        self.file_structure = FileStructure(self.fetch_lambda_paths())

        validate_rapid_trigger(self.pipeline_definition, self.config.rAPId_config)

        # Create infrastructure resource block creators
        self.cloudevent_bridge_rule = CreateEventBridgeRule(
            self.config,
            self.aws_provider,
            self.environment,
            self.pipeline_definition.trigger,
        )

    def get_lambda_role_arn(self):
        return self.infra_stack_reference.require_output(LAMBDA_ROLE_ARN)

    def get_state_machine_role_arn(self):
        return self.infra_stack_reference.require_output(STATE_FUNCTION_ROLE_ARN)

    def get_cloudevent_trigger_role_arn(self):
        return self.infra_stack_reference.require_output(
            CLOUDEVENT_STATE_MACHINE_TRIGGER_ROLE_ARN
        )

    def create_rapid_client(self) -> UserPoolClient | RapidClient:
        trigger = self.pipeline_definition.trigger
        client_key = trigger.client_key
        rapid_client = CreateRapidClient(
            self.config, self.aws_provider, self.environment, trigger
        )
        if client_key is None:
            pipeline_name = self.file_structure.pipeline_name
            layer = self.file_structure.layer
            permissions = create_rapid_permissions(
                self.config, self.pipeline_definition, layer
            )
            return rapid_client.apply(pipeline_name, layer, permissions).client

        return rapid_client.fetch_secret().client

    def apply(self):
        rapid_client = None
        if self.pipeline_definition.trigger is not None and isinstance(
            self.pipeline_definition.trigger, rAPIdTrigger
        ):
            rapid_client = self.create_rapid_client()

        lambda_paths = self.lambda_function_paths()
        lambda_paths.apply(
            lambda names: [
                self.apply_lambda_function(name, rapid_client).apply() for name in names
            ]
        ).apply(
            lambda outputs: {
                output.name: output.lambda_function.arn for output in outputs
            }
        ).apply(
            lambda lambda_map: self.apply_state_machine(lambda_map).apply()
        ).apply(
            lambda state_machine_outputs: self.apply_state_machine_trigger(
                state_machine_outputs
            )
            if self.pipeline_definition.trigger is not None
            else None
        )

    def fetch_lambda_paths(self) -> list[str]:
        initial = self.pipeline_definition.file_path.strip("__main__.py")
        path_to_search = os.path.join(initial, "*", LAMBDA_HANDLER_FILE)
        return [
            path.split(f"/{self.config.source_code_folder}/")[-1]
            for path in glob.glob(path_to_search)
        ]

    def lambda_function_paths(self):
        return pulumi.Output.from_input(
            [lambda_path for lambda_path in self.file_structure.lambda_paths]
        )

    def apply_lambda_function(
        self, lambda_path: str, rapid_client: UserPoolClient
    ) -> CreatePipelineLambdaFunction:
        return CreatePipelineLambdaFunction(
            config=self.config,
            aws_provider=self.aws_provider,
            environment=self.environment,
            universal_stack_reference=self.universal_stack_reference,
            lambda_role=self.lambda_role_arn,
            function_name=extract_lambda_name_from_filepath(lambda_path),
            code_path=os.path.dirname(lambda_path),
            rapid_client=rapid_client,
        )

    def apply_state_machine(self, lambdas: list[Function]):
        return CreatePipelineStateMachine(
            self.config,
            self.aws_provider,
            self.environment,
            self.file_structure.pipeline_name,
            self.pipeline_definition,
            lambdas,
            self.state_machine_role_arn,
        )

    def apply_state_machine_trigger(
        self, state_machine_outputs: CreatePipelineStateMachine.Output
    ):
        self.cloudevent_bridge_rule.exec()
        cloudevent_bridge_target = CreateEventBridgeTarget(
            self.config,
            self.aws_provider,
            self.environment,
            self.file_structure.pipeline_name,
            self.pipeline_definition,
            self.cloudevent_bridge_rule.outputs.cloudwatch_event_rule.name,
            self.cloudevent_trigger_role_arn,
            state_machine_outputs.state_machine.arn,
        )
        cloudevent_bridge_target.exec()

    def generate_pipeline_name_from_directory(self):
        path = self.pipeline_definition.file_path
        matcher = f"{self.config.config_repo_path}/src"
        return path_to_name(re.split(matcher, path)[-1].replace("/__main__.py", ""))
