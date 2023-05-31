# 10ds-core-pipelines

## Environment Variables

```
AWS_ACCOUNT=745078845594
AWS_REGION=eu-west-2
ENVIRONMENT=dev

INFRA_BUCKET=s3://ten-ds-pulumi-state
CONFIG_REPO_PATH=../10ds-core-pipelines-config
UNIVERSAL_STACK_NAME=universal
INFRA_STACK_NAME=infra

PULUMI_CONFIG_PASSPHRASE=
```

## Installing all required in `.venv`

You need to cd into `10ds-core-pipelines-config` and when in the `.venv` you need to install `pip install -e .` to install the `10ds-core-pipelines-config` repo into the venv. This will allow for the custom create config functions to be found.