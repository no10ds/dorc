import os

import pulumi
import pulumi_aws as aws

from utils.abstracts import InfrastructureCreateBlock


class CreatePipelineLambda(InfrastructureCreateBlock):
    # TODO: Move these parameters into a model
    def __init__(self, lambda_name: str, source_path: str) -> None:
        self.lambda_name = lambda_name
        self.source_path = source_path

    def apply(self, lambda_role, image):
        return aws.lambda_.Function(
            resource_name=self.lambda_name,
            role=lambda_role,
            runtime=None,
            handler=None,
            package_type="Image",
            image_uri=image,
        )
