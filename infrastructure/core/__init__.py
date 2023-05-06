import os
import pulumi

from infrastructure.core.lambdas import CreatePipelineLambda
from infrastructure.core.state_machine import CreatePipelineStateMachine

# TODO: Probably move out of __init__
class CreatePipeline():

    def __init__(self, file_path: str, pipeline_name: str, lambda_role, state_machine_role) -> None:
        # TODO: We probably want to pass in the class instance of the universal infrastructure
        # TODO: We want to pass in the pipeline configuration setting and perform validation
        # on this
        # TODO: Probably want to perform some validation on these variables?
        self.file_path = file_path
        self.pipeline_name = pipeline_name
        self.lambda_role = lambda_role
        self.state_machine_role = state_machine_role

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
        # Apply the lambdas based on the folder structure for the caller
        for root, dirs, _ in os.walk(self.src_dir):
            if (root != self.src_dir) and (len(dirs) == 0):
                lambda_name = self.extract_lambda_name_from_top_dir(root)

                # TODO: Is creating a new class instance here everytime overkill?
                # If not how can we create an array of them and chain the applies?
                new_pipeline_lambda = CreatePipelineLambda(lambda_name, root)
                function = new_pipeline_lambda.apply(self.lambda_role)

                self.created_lambdas[lambda_name] = function
                # TODO: Is this needed?
                pulumi.export(f"{lambda_name}_arn", function.arn)

    def apply_state_machine(self):
        config = [
            {
                "lambda_name": "example_default_lambda1",
                "next": "example_default_lambda2"
            },
            {
                "lambda_name": "example_default_lambda2",
                "next": None
            }
        ]

        new_state_machine = CreatePipelineStateMachine(self.pipeline_name, self.created_lambdas, config)
        new_state_machine.apply(self.state_machine_role)

    def extract_lambda_name_from_top_dir(self, root_dir: str) -> str:
        # TODO: Alot of this is hardcoded and is dependant on the folder structure
        # being exactly what we currently have defined
        directory = root_dir.replace("/src", "")
        splits = directory.split("/")
        return f"{splits[-3]}_{splits[-2]}_{splits[-1]}"