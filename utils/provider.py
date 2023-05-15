from pulumi_aws import Provider


def create_aws_provider(region: str, tags: dict | None):
    tags = {} if tags is None else tags
    return Provider(
        resource_name="aws_provider", region=region, default_tags={"tags": tags}
    )
