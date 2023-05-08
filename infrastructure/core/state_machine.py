import json
import pulumi
import pulumi_aws as aws

from typing import Dict

from infrastructure.core.models.config import Config, NextPipeline, NextPipelineTypes
from utils.abstracts import InfrastructureCreateBlock


class CreatePipelineStateMachine(InfrastructureCreateBlock):
    def __init__(self, lambdas_dict: Dict, config: Config) -> None:
        self.lambdas_dict = lambdas_dict
        self.config = config

        # TODO: We probably want to do some validation of the config agaisnt the lambdas dict
        # they can't specify a key in the config that is not actually a deployed lambda

    def apply(self, state_machine_role):
        state_machine_definition = pulumi.Output.all(
            [value.arn for value in self.lambdas_dict.values()]
        ).apply(lambda arns: self.create_state_machine_definition(arns))

        self.state_machine = aws.sfn.StateMachine(
            resource_name=self.config.pipeline_name,
            role_arn=state_machine_role,
            definition=state_machine_definition,
        )

    def create_state_machine_definition(self, arns: list):
        lambda_names = self.lambdas_dict.keys()
        name_to_arn_map = dict(zip(lambda_names, arns[0]))
        states_map = {}

        for pipeline in self.config.pipelines:
            # TODO: When defining a state function as the next trigger we don't need a function name
            # handle this case within the model and within this code
            function_name = pipeline.function_name
            next_function = pipeline.next_function

            if isinstance(next_function, NextPipeline):
                next_function_type = next_function.type

                if next_function_type == NextPipelineTypes.function:
                    # Create a simple lambda function next trigger
                    _map = self.create_lambda_next_trigger_state(
                        name_to_arn_map[function_name], next_function.name
                    )

                elif next_function_type == NextPipelineTypes.pipeline:
                    # This function wants to call another state machine
                    _map = self.create_state_machine_definition(next_function.name)
            else:
                # Create a simple lambda function next trigger
                _map = self.create_lambda_next_trigger_state(
                    name_to_arn_map[function_name], next_function
                )

            states_map[function_name] = _map

        # TODO: Define this comment in the wider configuration passed into class
        return f"""{{
            "Comment": "Example state machine function",
            "StartAt": "{self.config.pipelines[0].function_name}",
            "States": {json.dumps(states_map)}
        }}"""

    def create_lambda_next_trigger_state(self, arn, next_function):
        _map = {"Type": "Task", "Resource": arn}

        if next_function is None:
            _map["End"] = True
        else:
            _map["Next"] = next_function

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

    def get_state_machine_arn(self):
        return self.state_machine.arn
