from pulumi_aws import Provider


def create_aws_provider(region: str):
    return Provider(
        resource_name="aws_provider",
        region=region,
        skip_credentials_validation=True,
        skip_metadata_api_check=False,
    )
