import os
import pulumi

from typing import Dict
from pydantic import ValidationError

from infrastructure.core.lambdas import CreatePipelineLambda
from infrastructure.core.state_machine import CreatePipelineStateMachine
from infrastructure.core.config_model import Config

class CreatePipeline():

    def __init__(self, file_path: str, pipeline_name: str, config: Dict) -> None:
        # TODO: Probably want to perform some validation on these variables?
        self.file_path = file_path
        self.pipeline_name = pipeline_name

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
        top_dir = os.path.dirname(self.file_path)
        # TODO: Is hard coding this 'src' okay?
        self.src_dir = os.path.abspath(os.path.join(top_dir, 'src'))

    def apply(self):
        self.apply_lambdas()
        self.apply_state_machine()

    def apply_lambdas(self):
        lambda_role = self.universal_stack_reference.get_output("lambda_role_arn")

        # Apply the lambdas based on the folder structure for the caller
        for root, dirs, _ in os.walk(self.src_dir):
            if (root != self.src_dir) and (len(dirs) == 0):
                lambda_name = self.extract_lambda_name_from_top_dir(root)
                function = CreatePipelineLambda(lambda_name, root).apply(lambda_role)
                self.created_lambdas[lambda_name] = function

    def apply_state_machine(self):
        state_machine_role = self.universal_stack_reference.get_output("state_function_role_arn")
        CreatePipelineStateMachine(self.pipeline_name, self.created_lambdas, self.config).apply(state_machine_role)

    def extract_lambda_name_from_top_dir(self, root_dir: str) -> str:
        # TODO: Alot of this is hardcoded and is dependant on the folder structure
        # being exactly what we currently have defined
        directory = root_dir.replace("/src", "")
        splits = directory.split("/")
        return f"{splits[-3]}_{splits[-2]}_{splits[-1]}"