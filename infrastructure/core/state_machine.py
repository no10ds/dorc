import json

import pulumi
import pulumi_aws as aws

from pulumi import ResourceOptions
from pulumi_aws import Provider

from infrastructure.core.models.definition import (
    PipelineDefinition,
    NextFunction,
    NextFunctionTypes,
)

from utils.abstracts import ResourceCreateBlock
from utils.config import Config


class CreatePipelineStateMachine(ResourceCreateBlock):
    def __init__(
        self,
        config: Config,
        aws_provider: Provider,
        environment: str | None,
        pipeline_name: str,
        pipeline_definition: PipelineDefinition,
        lambdas_dict: dict,
        state_machine_role,
    ) -> None:
        super().__init__(config, aws_provider, environment)
        self.pipeline_name = pipeline_name
        self.pipeline_definition = pipeline_definition
        self.lambdas_dict = lambdas_dict
        self.state_machine_role = state_machine_role
        self.project = self.config.project

    def apply(self):
        state_machine_definition = pulumi.Output.all(
            [value.arn for value in self.lambdas_dict.values()]
        ).apply(lambda arns: self.create_state_machine_definition(arns))

        name = f"{self.project}-{self.environment}-{self.pipeline_name}"
        return aws.sfn.StateMachine(
            resource_name=name,
            name=name,
            role_arn=self.state_machine_role,
            definition=state_machine_definition,
            opts=ResourceOptions(provider=self.aws_provider),
        )

    def create_state_machine_definition(self, arns: list):
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
            "Comment": "Example state machine function",
            "StartAt": "{start_function_name}",
            "States": {json.dumps(states_map)}
        }}"""

    def create_lambda_next_trigger_state(self, arn: str, next_function_name: str):
        _map = {"Type": "Task", "Resource": arn}

        if next_function_name is None:
            _map["End"] = True
        else:
            next_function_name = self.create_function_name(next_function_name)
            _map["Next"] = next_function_name

        return _map

    def create_pipeline_next_trigger_state(self, next_function):
        # TODO: This function needs more work and greater thinking - first we don't want the user to have to pass
        # in the state machine arn, they just want to pass the name and we handle the rest
        # second is having this as the termination step correct?
        _map = {
            "Type": "Task",
            "Resource": "arn:aws:states:::states:startExecution.sync:2",
            "Parameters": {"StateMachineArn": next_function},
            "End": True,
        }

        return _map

    def create_function_name(self, name) -> str:
        return f"{self.pipeline_name}_{name}".replace("-", "_")
