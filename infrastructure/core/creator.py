import os
import pulumi
import pulumi_aws as aws
import pulumi_docker as docker

from git.repo import Repo
from typing import Dict
from pydantic import ValidationError

from infrastructure.core.lambdas import CreatePipelineLambda
from infrastructure.core.state_machine import CreatePipelineStateMachine
from infrastructure.core.event_bridge import (
    CreateEventBridgeRule,
    CreateEventBridgeTarget,
)
from infrastructure.core.ecr import CreateECRRepo
from infrastructure.core.models.config import Config, CloudwatchS3Trigger

repo = Repo(search_parent_directories=True)


class CreatePipeline:
    def __init__(self, config: Dict | Config) -> None:
        try:
            if isinstance(config, dict):
                self.config = Config.parse_obj(config)
            else:
                self.config = config
        except ValidationError as e:
            # TODO: Probably want a custom error here
            raise Exception(str(e))

        universal_stack_name = os.getenv("UNIVERSAL_STACK_NAME", "universal")
        self.universal_stack_reference = pulumi.StackReference(universal_stack_name)
        self.created_lambdas = {}

        self.create_source_directory()

    def create_source_directory(self):
        top_dir = os.path.dirname(self.config.file_path)
        # TODO: Is hard coding this 'src' okay?
        self.src_dir = os.path.abspath(os.path.join(top_dir, "src"))

    def apply(self):
        self.apply_ecr_repo()
        self.authenticate_to_ecr_repo()

        self.ecr_repo.get_repo_url().apply(
            lambda repo_url: self.build_and_deploy_folder_structure_functions(repo_url)
        ).apply(lambda _: self.apply_state_machine())

        # The state machine can be triggered by a cloudwatch event trigger
        if self.config.cloudwatch_trigger is not None:
            self.apply_cloudwatch_state_machine_trigger()

    def build_and_deploy_folder_structure_functions(self, repo_url: str):
        lambda_role = self.universal_stack_reference.get_output("lambda_role_arn")

        for root, dirs, _ in os.walk(self.src_dir):
            if (root != self.src_dir) and (len(dirs) == 0):
                lambda_name = self.extract_lambda_name_from_top_dir(root)
                code_path = self.extract_lambda_source_dir_from_top_dir(root)
                commit = self.get_git_short_commit_head()
                image_tag = f"{lambda_name}_{commit}"
                image = f"{repo_url}:{image_tag}"

                # TODO: Probs want this path as a configuration object (within Universal)?
                dockerfile = f"{os.getenv('CONFIG_REPO_PATH')}/src/Dockerfile"

                # Build and push lambda Docker image to ecr
                docker.Image(
                    resource_name=f"{self.config.pipeline_name}_{lambda_name}_image",
                    build=docker.DockerBuildArgs(
                        dockerfile=dockerfile,
                        platform="linux/amd64",
                        args={"CODE_PATH": code_path},
                        context=os.getenv("CONFIG_REPO_PATH"),
                        cache_from=docker.CacheFromArgs(images=[image]),
                    ),
                    image_name=image,
                    skip_push=False,
                    registry=docker.RegistryArgs(
                        server=repo_url,
                        password=self.registry_info.password,
                        username=self.registry_info.user_name,
                    ),
                )

                # Create lambda function from Docker image
                function = CreatePipelineLambda(lambda_name, root, image).apply(
                    lambda_role
                )
                self.created_lambdas[lambda_name] = function

    def apply_ecr_repo(self):
        self.ecr_repo = CreateECRRepo(self.config.pipeline_name)
        self.ecr_repo.apply()

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
        self.event_bridge_rule = CreateEventBridgeRule(trigger_config)
        self.event_bridge_rule.apply()
        self.event_bridge_target = CreateEventBridgeTarget(
            self.universal_stack_reference,
            f"{self.config.pipeline_name}-cloudevent-trigger-target",
            self.event_bridge_rule.get_event_bridge_name(),
            self.state_machine.get_state_machine_arn(),
        )
        self.event_bridge_target.apply()

    def authenticate_to_ecr_repo(self):
        self.registry_info = self.ecr_repo.get_repo_registry_id().apply(
            lambda registry_id: aws.ecr.get_authorization_token(registry_id=registry_id)
        )

    def add_function_to_created_lambdas(self, lambda_name, function):
        self.created_lambdas[lambda_name] = function

    def extract_lambda_name_from_top_dir(self, root_dir: str) -> str:
        # TODO: Alot of this is hardcoded and is dependant on the folder structure
        # being exactly what we currently have defined
        directory = root_dir.replace("/src", "")
        splits = directory.split("/")
        return f"{splits[-3]}_{splits[-2]}_{splits[-1]}"

    def extract_lambda_source_dir_from_top_dir(self, root_dir: str) -> str:
        # TODO: Alot of this is hardcoded and is dependant on the folder structure
        # being exactly what we currently have defined
        directory = root_dir.replace("/src", "")
        splits = root_dir.split("/")
        return f"{splits[-5]}/{splits[-4]}/{splits[-3]}/{splits[-2]}/{splits[-1]}"

    def get_git_short_commit_head(self):
        return repo.head.object.hexsha[:6]
