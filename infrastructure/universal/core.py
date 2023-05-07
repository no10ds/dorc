import pulumi_aws as aws


def create_code_storage_bucket(bucket_name: str):
    aws.s3.Bucket(
        "step-functions-code-storage-bucket", bucket=bucket_name, acl="private"
    )


def create_cloudwatch_log_group():
    aws.cloudwatch.LogGroup("pipelines-log-group")
