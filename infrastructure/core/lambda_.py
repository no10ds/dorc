import pulumi_aws as aws

from pulumi import ResourceOptions
from pulumi_aws import Provider
from pulumi_docker import Image

from utils.abstracts import ResourceCreateBlock
from utils.config import Config


class CreatePipelineLambdaFunction(ResourceCreateBlock):
    def __init__(
        self,
        config: Config,
        aws_provider: Provider,
        environment: str | None,
        lambda_role,
        function_name: str,
    ) -> None:
        super().__init__(config, aws_provider, environment)

        self.project = self.config.project
        self.lambda_role = lambda_role
        self.function_name = function_name

    def apply(self, image: Image):
        security_group = self.create_lambda_security_group()
        lambda_ = self.create_lambda(security_group, image)
        return lambda_

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

    def create_lambda(self, security_group, image: Image):
        name = f"{self.project}-{self.environment}-{self.function_name}"
        return aws.lambda_.Function(
            resource_name=name,
            name=name,
            role=self.lambda_role,
            runtime=None,
            handler=None,
            package_type="Image",
            image_uri=image.base_image_name,
            vpc_config=aws.lambda_.FunctionVpcConfigArgs(
                security_group_ids=[security_group.id],
                subnet_ids=self.config.private_subnet_ids,
            ),
            opts=ResourceOptions(provider=self.aws_provider),
        )
