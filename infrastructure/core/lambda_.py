import pulumi_aws as aws

from pulumi import ResourceOptions
from pulumi_aws import Provider
from pulumi_aws.ec2 import SecurityGroup
from pulumi_aws.lambda_ import Function
from pulumi_docker import Image

from utils.abstracts import CreateResourceBlock
from utils.config import Config


class CreatePipelineLambdaFunction(CreateResourceBlock):
    class Output(CreateResourceBlock.Output):
        security_group: SecurityGroup
        lambda_function: Function

    def __init__(
        self,
        config: Config,
        aws_provider: Provider,
        environment: str | None,
        lambda_role,
        function_name: str,
        image: Image,
    ) -> None:
        super().__init__(config, aws_provider, environment)
        self.project = self.config.project
        self.lambda_role = lambda_role
        self.function_name = function_name
        self.image = image

    def apply(self) -> Output:
        security_group = self.create_lambda_security_group()
        lambda_ = self.create_lambda(security_group)

        return self.Output(security_group=security_group, lambda_function=lambda_)

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

    def create_lambda(self, security_group):
        name = f"{self.project}-{self.environment}-{self.function_name}"
        return aws.lambda_.Function(
            resource_name=name,
            name=name,
            role=self.lambda_role,
            runtime=None,
            handler=None,
            package_type="Image",
            image_uri=self.image.base_image_name,
            vpc_config=aws.lambda_.FunctionVpcConfigArgs(
                security_group_ids=[security_group.id],
                subnet_ids=self.config.private_subnet_ids,
            ),
            opts=ResourceOptions(provider=self.aws_provider),
        )

    def export(self):
        pass
