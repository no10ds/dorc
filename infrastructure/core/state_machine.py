import boto3
import json

import pulumi
import pulumi_aws as aws

from pulumi import ResourceOptions
from pulumi_aws import Provider
from pulumi_aws.lambda_ import Function
from pulumi_aws.sfn import StateMachine

from infrastructure.core.models.definition import (
    PipelineDefinition,
    NextFunction,
    NextFunctionTypes,
)

from utils.abstracts import CreateResourceBlock
from utils.config import Config
from utils.exceptions import PipelineDoesNotExistException


class CreatePipelineStateMachine(CreateResourceBlock):
    class Output(CreateResourceBlock.Output):
        state_machine: StateMachine

    def __init__(
        self,
        config: Config,
        aws_provider: Provider,
        environment: str | None,
        pipeline_name: str,
        pipeline_definition: PipelineDefinition,
        lambda_name_to_arn_map: dict,
        state_machine_role,
        step_functions_client=boto3.client("stepfunctions"),
    ) -> None:
        super().__init__(config, aws_provider, environment)
        self.pipeline_name = pipeline_name
        self.pipeline_definition = pipeline_definition
        self.lambda_name_to_arn_map = lambda_name_to_arn_map
        self.state_machine_role = state_machine_role
        self.project = self.config.project
        self.step_functions_client = step_functions_client

    def apply(self) -> Output:
        state_machine_definition = pulumi.Output.from_input(
            self.lambda_name_to_arn_map
        ).apply(lambda arns: self.create_state_machine_definition(arns))
        name = f"{self.project}-{self.environment}-{self.pipeline_name}"
        state_machine = aws.sfn.StateMachine(
            resource_name=name,
            name=name,
            role_arn=self.state_machine_role,
            definition=state_machine_definition,
            opts=ResourceOptions(provider=self.aws_provider),
        )

        return self.Output(state_machine=state_machine)

    def create_state_machine_definition(self, name_to_arn_map: dict):
        states_map = {}

        for pipeline in self.pipeline_definition.functions:
            # TODO: When defining a state function as the next trigger we don't need a function name
            # handle this case within the model and within this code
            next_function = pipeline.next_function

            if isinstance(next_function, NextFunction):
                next_function_type = next_function.type
                next_function_name = next_function.name

                if next_function_type == NextFunctionTypes.FUNCTION:
                    # Create a simple lambda function next trigger
                    _map = self.create_lambda_next_trigger_state(
                        name_to_arn_map[pipeline.name], next_function_name
                    )

                elif next_function_type == NextFunctionTypes.PIPELINE:
                    # This function wants to call another state machine
                    _map = self.create_pipeline_next_trigger_state(next_function_name)
            else:
                # Create a simple lambda function next trigger
                _map = self.create_lambda_next_trigger_state(
                    name_to_arn_map[pipeline.name], next_function
                )

            states_map[pipeline.name] = _map

        start_function_name = self.pipeline_definition.functions[0].name

        return f"""{{
            "Comment": "{self.pipeline_definition.description}",
            "StartAt": "{start_function_name}",
            "States": {json.dumps(states_map)}
        }}"""

    def create_lambda_next_trigger_state(
        self, arn: str, next_function_name: str | None
    ):
        _map = {"Type": "Task", "Resource": arn}

        if next_function_name is None:
            _map["End"] = True
        else:
            _map["Next"] = next_function_name

        return _map

    def fetch_step_function_arn_from_name(self, name: str) -> str:
        response = self.step_functions_client.list_state_machines()["stateMachines"]
        for sfn in response:
            if sfn["name"] == name:
                arn = sfn["stateMachineArn"]
                return arn
        raise PipelineDoesNotExistException(f"Could not find pipeline {name}")

    def create_pipeline_next_trigger_state(self, next_function: str):
        next_function_arn = self.fetch_step_function_arn_from_name(next_function)
        _map = {
            "Type": "Task",
            "Resource": "arn:aws:states:::states:startExecution.sync:2",
            "Parameters": {"StateMachineArn": next_function_arn},
            "End": True,
        }

        return _map

    def export(self):
        pass
