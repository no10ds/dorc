import os

import pulumi
import pulumi_aws as aws

# TODO: Probably want this to extend a abstract pipeline create class?
class CreatePipelineLambda():

    def __init__(self, lambda_name: str, source_path: str) -> None:
        self.lambda_name = lambda_name
        self.source_path = source_path

        top_dir = os.path.dirname(__file__)
        src_dir = os.path.abspath(os.path.join(top_dir, 'src'))

    def apply(self, lambda_role):
        return aws.lambda_.Function(
            resource_name=self.lambda_name,
            role=lambda_role,
            runtime="python3.9",
            handler="lambda.handler",
            code=pulumi.AssetArchive({
                '.': pulumi.FileArchive(self.source_path)
            })
        )