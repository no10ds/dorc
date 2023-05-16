from pulumi_aws import Provider


def create_aws_provider(region: str):
    return Provider(resource_name="aws_provider", region=region)
