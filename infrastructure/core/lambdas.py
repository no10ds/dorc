import os

import pulumi
import pulumi_aws as aws
from typing import Any
from pulumi import Output

from utils.abstracts import InfrastructureCreateBlock


class CreatePipelineLambda(InfrastructureCreateBlock):
    # TODO: Move these parameters into a model
    def __init__(
        self, project: Output[Any], lambda_name: str, source_path: str
    ) -> None:
        self.project = project
        self.lambda_name = lambda_name
        self.source_path = source_path

    def apply(self, lambda_role, image):
        return self.project.apply(
            lambda project: aws.lambda_.Function(
                resource_name=f"{project}_{self.lambda_name}",
                name=f"{project}_{self.lambda_name}",
                role=lambda_role,
                runtime=None,
                handler=None,
                package_type="Image",
                image_uri=image,
            )
        )

    # def apply(self, lambda_role: Output[str], image: Output[str]):
    #     return pulumi.Output.all(self.project, lambda_role, image).apply(
    #         lambda outputs: aws.lambda_.Function(
    #             resource_name=f"{outputs[0]}_{self.lambda_name}",
    #             name=f"{outputs[0]}_{self.lambda_name}",
    #             role=outputs[1],
    #             runtime=None,
    #             handler=None,
    #             package_type="Image",
    #             image_uri=outputs[2],
    #         )
    #     )
