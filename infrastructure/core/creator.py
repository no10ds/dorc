import os
import re
import pulumi
import pulumi_aws as aws
import pulumi_docker as docker

from pulumi import ResourceOptions
from pulumi_docker import Image
from pydantic import ValidationError
from checksumdir import dirhash

from infrastructure.core.event_bridge import (
    CreateEventBridgeRule,
    CreateEventBridgeTarget,
)
from infrastructure.core._lambda import CreatePipelineLambdaFunction
from infrastructure.core.state_machine import CreatePipelineStateMachine
from infrastructure.core.models.definition import PipelineDefinition
from infrastructure.universal.ecr import CreateEcrResource
from utils.abstracts import CreateInfrastructureBlock
from utils.config import Config
from utils.constants import (
    LAMBDA_ROLE_ARN,
    STATE_FUNCTION_ROLE_ARN,
    CLOUDEVENT_STATE_MACHINE_TRIGGER_ROLE_ARN,
)
from utils.exceptions import InvalidPipelineDefinitionException


class CreatePipeline(CreateInfrastructureBlock):
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
        infra_stack_name = (
            f"{os.getenv('INFRA_STACK_NAME', 'infra')}-{self.environment}"
        )

        self.universal_stack_reference = pulumi.StackReference(universal_stack_name)
        self.infra_stack_reference = pulumi.StackReference(infra_stack_name)

        self.lambda_role_arn = self.infra_stack_reference.require_output(
            LAMBDA_ROLE_ARN
        )

        self.lambda_role_arn = self.get_lambda_role_arn()
        self.state_machine_role_arn = self.get_state_machine_role_arn()
        self.cloudevent_trigger_role_arn = self.get_cloudevent_trigger_role_arn()

        self.pipeline_name = self.generate_pipeline_name_from_directory()

        self.created_lambdas = {}
        self.src_dir = self.fetch_source_directory_name()

        # Create infrastructure resource block creators
        self.cloudevent_bridge_rule = CreateEventBridgeRule(
            self.config,
            self.aws_provider,
            self.environment,
            self.pipeline_definition.cloudwatch_trigger,
        )

    def get_lambda_role_arn(self):
        return self.infra_stack_reference.require_output(LAMBDA_ROLE_ARN)

    def get_state_machine_role_arn(self):
        return self.infra_stack_reference.require_output(STATE_FUNCTION_ROLE_ARN)

    def get_cloudevent_trigger_role_arn(self):
        return self.infra_stack_reference.require_output(
            CLOUDEVENT_STATE_MACHINE_TRIGGER_ROLE_ARN
        )

    def fetch_source_directory_name(self):
        top_dir = os.path.dirname(self.pipeline_definition.file_path)
        return os.path.abspath(os.path.join(top_dir, self.config.source_code_path))

    def apply(self):
        self.authenticate_to_ecr_repo()
        ecr_repo_url_output = self.universal_stack_reference.require_output(
            CreateEcrResource.create_repository_url_export_key(self.pipeline_name)
        )

        ecr_repo_url_output.apply(
            lambda url: self.build_and_deploy_folder_structure_functions(url)
        ).apply(lambda _: self.apply_state_machine().apply()).apply(
            lambda state_machine_outputs: self.apply_cloudwatch_state_machine_trigger(
                state_machine_outputs
            )
            if self.pipeline_definition.cloudwatch_trigger is not None
            else None
        )

    def build_and_deploy_folder_structure_functions(self, url: str):
        for root, dirs, _ in os.walk(self.src_dir):
            if root != self.src_dir and len(dirs) == 0:
                lambda_name = self.extract_lambda_name_from_top_dir(root)
                image = self.apply_docker_image_build_and_push(url, lambda_name, root)
                lambda_function = self.apply_lambda_function(lambda_name, image)

                self.created_lambdas[
                    lambda_name
                ] = lambda_function.outputs.lambda_function

    def apply_docker_image_build_and_push(
        self, url: str, lambda_name: str, root: str
    ) -> Image:
        code_path = self.extract_lambda_source_dir_from_top_dir(root)
        code_hash = dirhash(root)
        image = f"{url}:{lambda_name}_{code_hash}"

        # TODO: Do we want this path as a configuration object?
        dockerfile = f"{os.getenv('CONFIG_REPO_PATH')}/src/Dockerfile"

        return docker.Image(
            resource_name=f"{self.pipeline_name}_{lambda_name}_image",
            build=docker.DockerBuildArgs(
                dockerfile=dockerfile,
                platform="linux/amd64",
                args={"CODE_PATH": code_path, "BUILDKIT_INLINE_CACHE": "1"},
                builder_version="BuilderBuildKit",
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

    def apply_lambda_function(
        self, lambda_name: str, image: Image
    ) -> CreatePipelineLambdaFunction:
        return CreatePipelineLambdaFunction(
            self.config,
            self.aws_provider,
            self.environment,
            self.lambda_role_arn,
            lambda_name,
            image,
        )

    def apply_state_machine(self):
        return CreatePipelineStateMachine(
            self.config,
            self.aws_provider,
            self.environment,
            self.pipeline_name,
            self.pipeline_definition,
            self.created_lambdas,
            self.state_machine_role_arn,
        )

    def apply_cloudwatch_state_machine_trigger(
        self, state_machine_outputs: CreatePipelineStateMachine.Output
    ):
        self.cloudevent_bridge_rule.exec()
        cloudevent_bridge_target = CreateEventBridgeTarget(
            self.config,
            self.aws_provider,
            self.environment,
            self.pipeline_name,
            self.pipeline_definition,
            self.cloudevent_bridge_rule.outputs.cloudwatch_event_rule.name,
            self.cloudevent_trigger_role_arn,
            state_machine_outputs.state_machine.arn,
        )
        cloudevent_bridge_target.exec()

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
