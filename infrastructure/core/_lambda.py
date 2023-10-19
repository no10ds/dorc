import os

import pulumi
import pulumi_aws as aws
import pulumi_docker as docker

from checksumdir import dirhash
from pulumi_aws.lambda_ import Function
from pulumi_aws.cognito import UserPoolClient
from pulumi import ResourceOptions, StackReference

from utils.abstracts import CreateResourceBlock
from utils.config import Config
from infrastructure.universal.ecr import CreateEcrResource
from infrastructure.providers.rapid_client import RapidClient


class CreatePipelineLambdaFunction(CreateResourceBlock):
    class Output(CreateResourceBlock.Output):
        lambda_function: Function
        name: str

    def __init__(
        self,
        config: Config,
        aws_provider: aws.Provider,
        environment: str | None,
        universal_stack_reference: StackReference,
        lambda_role,
        function_name: str,
        code_path: str,
        rapid_client: UserPoolClient | RapidClient | None,
    ) -> None:
        super().__init__(config, aws_provider, environment)
        self.project = self.config.project
        self.universal_stack_reference = universal_stack_reference
        self.lambda_role = lambda_role
        self.function_name = function_name
        self.code_path = code_path
        self.rapid_client = rapid_client

    def authenticate_to_ecr_repo(self) -> aws.ecr.GetAuthorizationTokenResult:
        ecr_repo_id_output = self.universal_stack_reference.require_output(
            CreateEcrResource.create_repository_id_export_key(self.function_name)
        )
        return ecr_repo_id_output.apply(
            lambda id: aws.ecr.get_authorization_token(registry_id=id)
        )

    def apply(self) -> Output:
        registry_info = self.authenticate_to_ecr_repo()
        security_group = self.create_lambda_security_group()

        image = self.universal_stack_reference.require_output(
            CreateEcrResource.create_repository_url_export_key(self.function_name)
        ).apply(lambda url: self.apply_docker_image_build_and_push(registry_info, url))

        _lambda = self.create_lambda(security_group, image)
        lambda_folder_name = self.code_path.split("/")[-1]
        return self.Output(lambda_function=_lambda, name=lambda_folder_name)

    def apply_docker_image_build_and_push(
        self, registry_info: aws.ecr.GetAuthorizationTokenResult, url: str
    ) -> docker.Image:
        code_hash = dirhash(
            os.path.join(self.config.universal.source_code_path, self.code_path)
        )
        image = f"{url}:{code_hash}"

        return docker.Image(
            resource_name=f"{self.function_name}-image",
            build=docker.DockerBuildArgs(
                dockerfile=f"{self.config.universal.source_code_path}/Dockerfile",
                platform="linux/amd64",
                args={
                    "CODE_PATH": f"./src/{self.code_path}",
                    "BUILDKIT_INLINE_CACHE": "1",
                },
                builder_version="BuilderBuildKit",
                context=self.config.universal.config_repo_path,
                cache_from=docker.CacheFromArgs(images=[image]),
            ),
            image_name=image,
            skip_push=False,
            registry=docker.RegistryArgs(
                server=url,
                password=registry_info.password,
                username=registry_info.user_name,
            ),
            opts=ResourceOptions(self.aws_provider),
        )

    def create_lambda_security_group(self):
        name = f"{self.project}-{self.environment}-{self.function_name}-sg"
        return aws.ec2.SecurityGroup(
            resource_name=name,
            name=name,
            vpc_id=self.config.vpc_id,
            egress=[
                aws.ec2.SecurityGroupEgressArgs(
                    description="HTTPS outbound",
                    from_port=443,
                    to_port=443,
                    protocol="tcp",
                    cidr_blocks=["0.0.0.0/0"],
                )
            ],
            opts=ResourceOptions(provider=self.aws_provider),
        )

    def create_lambda(self, security_group, image: docker.Image):
        name = f"{self.project}-{self.environment}-{self.function_name}"
        return aws.lambda_.Function(
            resource_name=name,
            name=name,
            role=self.lambda_role,
            runtime=None,
            timeout=600,
            package_type="Image",
            image_uri=image.base_image_name,
            vpc_config=aws.lambda_.FunctionVpcConfigArgs(
                security_group_ids=[security_group.id],
                subnet_ids=self.config.private_subnet_ids,
            ),
            environment={
                "variables": {**self.create_rapid_environment_variables()},
            },
            opts=ResourceOptions(provider=self.aws_provider),
        )

    def create_rapid_environment_variables(self) -> dict:
        if self.rapid_client is None:
            return {}
        else:
            return {
                "RAPID_CLIENT_ID": self.rapid_client.id,
                "RAPID_CLIENT_SECRET": self.rapid_client.client_secret,
                "RAPID_URL": self.config.rAPId_config.url,
            }

    def export(self):
        pass
