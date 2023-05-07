import json
import pulumi
import pulumi_aws as aws

from typing import Dict

from infrastructure.core.config_model import Config

# TODO: Probably want this to extend a abstract pipeline create class?
class CreatePipelineStateMachine():

    def __init__(self, lambdas_dict: Dict, config: Config) -> None:
        self.lambdas_dict = lambdas_dict
        self.config = config

        # TODO: We probably want to do some validation of the config agaisnt the lambdas dict
        # they can't specify a key in the config that is not actually a deployed lambda

    def apply(self, state_machine_role):
        state_machine_definition = pulumi.Output.all([value.arn for value in self.lambdas_dict.values()]).apply(
            lambda arns: self.create_state_machine_definition(arns)
        )

        aws.sfn.StateMachine(
            resource_name=self.config.pipeline_name,
            role_arn=state_machine_role,
            definition=state_machine_definition
        )

    def create_state_machine_definition(self, arns: list):
        lambda_names = self.lambdas_dict.keys()
        name_to_arn_map = dict(zip(lambda_names, arns[0]))
        states_map = {}

        for pipeline in self.config.pipelines:
            function_name = pipeline.function_name
            next_function = pipeline.next_function

            states_map[function_name] = {
                "Type": "Task",
                "Resource": name_to_arn_map[function_name]
            }

            # They have not specified a next so we can assume this is the termination state
            if next_function is None:
                states_map[function_name]["End"] = True
            else:
                states_map[function_name]["Next"] = next_function

        # TODO: Define this comment in the wider configuration passed into class
        return f"""{{
            "Comment": "Example state machine function",
            "StartAt": "{self.config.pipelines[0].function_name}",
            "States": {json.dumps(states_map)}
        }}"""
