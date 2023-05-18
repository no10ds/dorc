import os
import re
import pulumi
import pulumi_aws as aws
import pulumi_docker as docker

from pulumi import ResourceOptions
from pydantic import ValidationError
from checksumdir import dirhash

from infrastructure.core.event_bridge import (
    CreateEventBridgeRule,
    CreateEventBridgeTarget,
)
from infrastructure.core.lambda_ import CreatePipelineLambdaFunction
from infrastructure.core.state_machine import CreatePipelineStateMachine
from infrastructure.core.models.definition import PipelineDefinition
from utils.abstracts import InfrastructureCreateBlock
from utils.config import Config
from utils.exceptions import InvalidPipelineDefinitionException


class CreatePipeline(InfrastructureCreateBlock):
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
        infra_stack_name = os.getenv("INFRA_STACK_NAME", "infra")
        self.universal_stack_reference = pulumi.StackReference(universal_stack_name)
        # TODO: Environment specific this
        self.infra_stack_reference = pulumi.StackReference(f"{infra_stack_name}-dev")

        # TODO: Change the name of these to arns
        self.lambda_role = self.infra_stack_reference.get_output("lambda_role_arn")
        self.state_machine_role = self.infra_stack_reference.get_output(
            "state_function_role_arn"
        )
        self.cloudevent_trigger_role = self.infra_stack_reference.get_output(
            "cloudevent_state_machine_trigger_role_arn"
        )

        self.pipeline_name = self.generate_pipeline_name_from_directory()

        self.created_lambdas = {}
        self.create_source_directory()

    def create_source_directory(self):
        top_dir = os.path.dirname(self.pipeline_definition.file_path)
        self.src_dir = os.path.abspath(
            os.path.join(top_dir, self.config.source_code_path)
        )

    def apply(self):
        self.authenticate_to_ecr_repo()

        ecr_repo_url_output = self.universal_stack_reference.get_output(
            f"ecr_repository_{self.pipeline_name}_url"
        )

        ecr_repo_url_output.apply(
            lambda url: self.build_and_deploy_folder_structure_functions(url)
        ).apply(lambda _: self.apply_state_machine()).apply(
            lambda _: self.apply_cloudwatch_state_machine_trigger()
            if self.pipeline_definition.cloudwatch_trigger is not None
            else None
        )

    def build_and_deploy_folder_structure_functions(self, url: str):
        for root, dirs, _ in os.walk(self.src_dir):
            if root != self.src_dir and len(dirs) == 0:
                lambda_name = self.extract_lambda_name_from_top_dir(root)
                code_path = self.extract_lambda_source_dir_from_top_dir(root)
                code_hash = dirhash(root)
                image = f"{url}:{lambda_name}_{code_hash}"

                # TODO: Probs want this path as a configuration object (within Universal)?
                dockerfile = f"{os.getenv('CONFIG_REPO_PATH')}/src/Dockerfile"

                dockered_image = docker.Image(
                    resource_name=f"{self.pipeline_name}_{lambda_name}_image",
                    build=docker.DockerBuildArgs(
                        dockerfile=dockerfile,
                        platform="linux/amd64",
                        args={"CODE_PATH": code_path, "BUILDKIT_INLINE_CACHE": "1"},
                        builder_version="BuilderBuildKit",
                        # TODO: Do we get this from envs or config?
                        context=os.getenv("CONFIG_REPO_PATH"),
                        cache_from=docker.CacheFromArgs(images=[image]),
                    ),
                    image_name=image,
                    skip_push=False,
                    registry=docker.RegistryArgs(
                        server=url,
                        password=self.registry_info.password,
                        username=self.registry_info.user_name,
                    ),
                    opts=ResourceOptions(self.aws_provider),
                )

                lambda_ = CreatePipelineLambdaFunction(
                    self.config,
                    self.aws_provider,
                    self.environment,
                    self.lambda_role,
                    lambda_name,
                )
                function = lambda_.apply(dockered_image)
                self.created_lambdas[lambda_name] = function

    def apply_state_machine(self):
        state_machine_creator = CreatePipelineStateMachine(
            self.config,
            self.aws_provider,
            self.environment,
            self.pipeline_name,
            self.pipeline_definition,
            self.created_lambdas,
            self.state_machine_role,
        )
        self.state_machine = state_machine_creator.apply()

    def apply_cloudwatch_state_machine_trigger(self):
        trigger_config = self.pipeline_definition.cloudwatch_trigger
        self.event_bridge_rule = CreateEventBridgeRule(
            self.config, self.aws_provider, self.environment, trigger_config
        )
        event_rule = self.event_bridge_rule.apply()
        self.event_bridge_target = CreateEventBridgeTarget(
            self.config,
            self.aws_provider,
            self.environment,
            self.pipeline_name,
            self.pipeline_definition,
            event_rule.name,
            self.state_machine,
            self.cloudevent_trigger_role,
        )
        self.event_bridge_target.apply()

    def authenticate_to_ecr_repo(self):
        ecr_repo_id_output = self.universal_stack_reference.get_output(
            f"ecr_repository_{self.pipeline_name}_id"
        )
        self.registry_info = ecr_repo_id_output.apply(
            lambda id: aws.ecr.get_authorization_token(registry_id=id)
        )

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

    def generate_pipeline_name_from_directory(self):
        path = self.pipeline_definition.file_path
        matcher = f"{self.config.config_repo_path}/src"
        return (
            re.split(matcher, path)[-1]
            .strip("/")
            .replace("/__main__.py", "")
            .replace("/", "-")
        )
