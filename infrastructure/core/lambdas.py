import os

import pulumi
import pulumi_aws as aws

from utils.abstracts import InfrastructureCreateBlock


class CreatePipelineLambda(InfrastructureCreateBlock):
    # TODO: Move these parameters into a model
    def __init__(self, lambda_name: str, source_path: str, image_url: str) -> None:
        self.lambda_name = lambda_name
        self.source_path = source_path
        self.image_url = image_url

    def apply(self, lambda_role):
        return aws.lambda_.Function(
            resource_name=self.lambda_name,
            role=lambda_role,
            runtime=None,
            handler=None,
            package_type="Image",
            image_uri=self.image_url,
        )
