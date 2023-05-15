import os

import pulumi
import pulumi_aws as aws
from typing import Any
from pulumi import Output

from utils.abstracts import InfrastructureCreateBlock


class CreatePipelineLambda(InfrastructureCreateBlock):
    # TODO: Move these parameters into a model
    def __init__(
        self, universal_stack_reference, lambda_name: str, source_path: str
    ) -> None:
        self.lambda_name = lambda_name
        self.source_path = source_path

        # Use universal outputs
        self.project = universal_stack_reference.get_output("project")
        self.private_subnet_ids = universal_stack_reference.get_output(
            "private_subnet_ids"
        )
        self.vpc_id = universal_stack_reference.get_output("vpc_id")

    def apply(self, lambda_role, image):
        return pulumi.Output.all(
            project=self.project,
            vpc_id=self.vpc_id,
            private_subnet_ids=self.private_subnet_ids,
            security_group_ids=self.create_lambda_security_group(),
        ).apply(
            lambda args: aws.lambda_.Function(
                resource_name=f"{args['project']}-{self.lambda_name}",
                name=f"{args['project']}-{self.lambda_name}",
                role=lambda_role,
                runtime=None,
                handler=None,
                package_type="Image",
                image_uri=image,
                vpc_config=aws.lambda_.FunctionVpcConfigArgs(
                    security_group_ids=[args["security_group_ids"].id],
                    subnet_ids=args["private_subnet_ids"],
                ),
            )
        )

    def create_lambda_security_group(self):
        # TODO: Probably want to provide this as a parameter to the config
        # Or create this one be default and have the ability to supply sg ids?
        return pulumi.Output.all(project=self.project, vpc_id=self.vpc_id).apply(
            lambda args: aws.ec2.SecurityGroup(
                resource_name=f"{args['project']}-{self.lambda_name}-sg",
                name=f"{args['project']}-{self.lambda_name}-sg",
                vpc_id=args["vpc_id"],
                egress=[
                    aws.ec2.SecurityGroupEgressArgs(
                        description="HTTPs outbound",
                        from_port=443,
                        to_port=443,
                        protocol="tcp",
                        cidr_blocks=["0.0.0.0/0"],
                    )
                ],
            )
        )
