All *dorc* creators require a python configuration model. Both configurations are defined as [Pydantic](https://pydantic.dev/) models.

## Universal Configuration

The universal configuration contains the values that are kept the same project wide and are not environment specific.

```python
from utils.config import UniversalConfig

UniversalConfig(
    region: str
    project: str
    config_repo_path: str
    tags: Optional[dict]
    source_code_path: Optional[str] = "src"
)
```

* `region` - The aws region in which all infrastructure will be deployed to
* `project` - Your high level project name
* `config_repo_path` - Relevant path from the *dorc* repository to your private source code repository
* `tags` - An optional dictionary of key-value tags to apply to every resource created
* `source_code_path` - The name of the folder within your private source repository that the pipeline definitions are saved. This value defaults to `src`

## Configuration

The second configuration model are for those values that you may wish to alter depending on which environment you are deploying to.

```python
from utils.config import Config

Config(
    universal: UniversalConfig
    vpc_id: pulumi.Output[str] | str
    private_subnet_ids: pulumi.Output[list[str]] | list[str]

    additional_lambda_role_policy_arn: Optional[pulumi.Output[str] | str]
    additional_state_function_role_policy_arn: Optional[pulumi.Output[str] | str]
    additional_cloudevent_state_machine_trigger_role_policy_arn: Optional[pulumi.Output[str] | str]
)
```

* `universal` - Your defined *dorc* universal configuration model
* `vpc_id` - The id of your aws vpc to deploy infrastructure to
* `private_subnet_ids` - List of aws private subnet ids to attach to the resources
* `additional_lambda_role_policy_arn` - By default *dorc* creates a lambda policy that is enough to get going with, however if you require specific access to different services within your lambdas you can create this policy yourself and pass *dorc* the aws arn which it will attach to it's default policy
* `additional_state_function_role_policy_arn` - The same as the lambda policy but attached to the default state machines policy instead
* `additional_cloudevent_state_machine_trigger_role_policy_arn` - The same as the lambda policy but attached to the default cloudevent trigger policy instead
