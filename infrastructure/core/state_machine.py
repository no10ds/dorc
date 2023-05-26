import boto3
import json

import pulumi
import pulumi_aws as aws

from pulumi import ResourceOptions
from pulumi_aws import Provider
from pulumi_aws.sfn import StateMachine

from infrastructure.core.models.definition import (
    PipelineDefinition,
    NextFunction,
    NextFunctionTypes,
)

from utils.abstracts import CreateResourceBlock
from utils.config import Config
from utils.exceptions import StepFunctionDoesNotExistException


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
        lambdas_dict: dict,
        state_machine_role,
        step_functions_client = boto3.client('stepfunctions')
    ) -> None:
        super().__init__(config, aws_provider, environment)
        self.pipeline_name = pipeline_name
        self.pipeline_definition = pipeline_definition
        self.lambdas_dict = lambdas_dict
        self.state_machine_role = state_machine_role
        self.project = self.config.project
        self.step_functions_client = step_functions_client

    def apply(self) -> Output:
        state_machine_definition = pulumi.Output.all(
            [value.arn for value in self.lambdas_dict.values()]
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

    def create_state_machine_definition(self, arns: list[list]):
        lambda_names = self.lambdas_dict.keys()
        name_to_arn_map = dict(zip(lambda_names, arns[0]))

        states_map = {}

        for pipeline in self.pipeline_definition.functions:
            # TODO: When defining a state function as the next trigger we don't need a function name
            # handle this case within the model and within this code
            function_name = self.create_function_name(pipeline.name)
            next_function = pipeline.next_function

            if isinstance(next_function, NextFunction):
                next_function_type = next_function.type
                next_function_name = next_function.name

                if next_function_type == NextFunctionTypes.FUNCTION:
                    # Create a simple lambda function next trigger
                    _map = self.create_lambda_next_trigger_state(
                        name_to_arn_map[function_name], next_function_name
                    )

                elif next_function_type == NextFunctionTypes.PIPELINE:
                    # This function wants to call another state machine
                    _map = self.create_pipeline_next_trigger_state(next_function_name)
            else:
                # Create a simple lambda function next trigger
                _map = self.create_lambda_next_trigger_state(
                    name_to_arn_map[function_name], next_function
                )

            states_map[function_name] = _map

        start_function_name = self.create_function_name(
            self.pipeline_definition.functions[0].name
        )

        # TODO: Define this comment in the wider configuration passed into class
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
            next_function_name = self.create_function_name(next_function_name)
            _map["Next"] = next_function_name

        return _map

    def fetch_step_function_arn_from_name(self, name: str) -> str:
        function_name = self.create_function_name(name)
        response = self.step_functions_client.list_state_machines()['stateMachines']
        for sfn in response:
            if sfn['name'] == function_name:
                arn = sfn['stateMachineArn']
                return arn
        raise StepFunctionDoesNotExistException(f"Could not find the set")

    def create_pipeline_next_trigger_state(self, next_function: str):
        next_function_arn = self.fetch_step_function_arn_from_name(next_function)
        _map = {
            "Type": "Task",
            "Resource": "arn:aws:states:::states:startExecution.sync:2",
            "Parameters": {"StateMachineArn": next_function_arn},
            "End": True,
        }

        return _map

    def create_function_name(self, name) -> str:
        return f"{self.pipeline_name}_{name}".replace("-", "_")

    def export(self):
        pass
