import os
import pulumi

from typing import Dict
from pydantic import ValidationError

from infrastructure.core.lambdas import CreatePipelineLambda
from infrastructure.core.state_machine import CreatePipelineStateMachine
from infrastructure.core.event_bridge import CreateEventBridge, CreateEventBridgeTarget
from infrastructure.core.models.config import Config


class CreatePipeline:
    def __init__(self, config: Dict) -> None:
        try:
            self.config = Config.parse_obj(config)
        except ValidationError as e:
            # TODO: Probably want a custom error here
            raise Exception(str(e))

        # TODO: Probably want this stack reference name as a config variable in the future
        self.universal_stack_reference = pulumi.StackReference("universal")

        # TODO: Is this the best name and variable structure for this?
        self.created_lambdas = {}

        self.create_source_directory()

    def create_source_directory(self):
        top_dir = os.path.dirname(self.config.file_path)
        # TODO: Is hard coding this 'src' okay?
        self.src_dir = os.path.abspath(os.path.join(top_dir, "src"))

    def apply(self):
        self.apply_lambdas()
        self.apply_state_machine()

        # The state machine can be triggered by a cloudwatch event trigger
        if self.config.cloudwatch_trigger is not None:
            self.apply_cloudwatch_state_machine_trigger()

    def apply_lambdas(self):
        lambda_role = self.universal_stack_reference.get_output("lambda_role_arn")

        # Apply the lambdas based on the folder structure for the caller
        for root, dirs, _ in os.walk(self.src_dir):
            if (root != self.src_dir) and (len(dirs) == 0):
                lambda_name = self.extract_lambda_name_from_top_dir(root)
                function = CreatePipelineLambda(lambda_name, root).apply(lambda_role)
                self.created_lambdas[lambda_name] = function

    def apply_state_machine(self):
        state_machine_role = self.universal_stack_reference.get_output(
            "state_function_role_arn"
        )
        self.state_machine = CreatePipelineStateMachine(
            self.created_lambdas, self.config
        )
        self.state_machine.apply(state_machine_role)

    def apply_cloudwatch_state_machine_trigger(self):
        trigger_config = self.config.cloudwatch_trigger
        self.event_bridge = CreateEventBridge(
            f"{self.config.pipeline_name}-cloudevent-trigger",
            trigger_config.bucket_name,
            trigger_config.key_prefix,
        )
        self.event_bridge.apply()
        self.event_bridge_target = CreateEventBridgeTarget(
            self.universal_stack_reference,
            f"{self.config.pipeline_name}-cloudevent-trigger-target",
            self.event_bridge.get_event_bridge_name(),
            self.state_machine.get_state_machine_arn(),
        )
        self.event_bridge_target.apply()

    def extract_lambda_name_from_top_dir(self, root_dir: str) -> str:
        # TODO: Alot of this is hardcoded and is dependant on the folder structure
        # being exactly what we currently have defined
        directory = root_dir.replace("/src", "")
        splits = directory.split("/")
        return f"{splits[-3]}_{splits[-2]}_{splits[-1]}"
