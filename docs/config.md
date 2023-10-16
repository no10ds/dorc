All *dorc* projects require two python configuration models, both defined as [Pydantic](https://pydantic.dev/) models.

## Universal Configuration

The universal configuration contains values that remain the same project-wide and are not environment-specific. Here is an example of the `UniversalConfig` model:

```python
from utils.config import UniversalConfig, LayerConfig

UniversalConfig(
    region: str
    project: str
    tags: Optional[dict]
    source_code_folder: Optional[str] = "src"
    rapid_layer_config: Optional[list[LayerConfig]] = None
)
```

* `region` - The AWS region to which all infrastructure will be deployed.
* `project` - Your high-level project name.
* `tags` - An optional dictionary of key-value tags to apply to every created resource.
* `source_code_folder` - The name of the folder within your private source repository where the pipeline definitions are saved. The default value is `src`.
* `rapid_layer_config` - An optional value that specifies the list of `LayerConfig` blocks that maps your *dorc* folder structure to your rAPId layers. See the [rAPId integration](/rapid_integration/#rapid-layer-configuration) for further information.

## Configuration

The second configuration model is for values that you may want to customize depending on the environment to which you are deploying. Here is an example of the `Config` model:

```python
from utils.config import Config, rAPIdConfig

Config(
    universal: UniversalConfig
    vpc_id: pulumi.Output[str] | str
    private_subnet_ids: pulumi.Output[list[str]] | list[str]

    rAPId_config: Optional[rAPIdConfig]

    additional_lambda_role_policy_arn: Optional[pulumi.Output[str] | str]
    additional_state_function_role_policy_arn: Optional[pulumi.Output[str] | str]
    additional_cloudevent_state_machine_trigger_role_policy_arn: Optional[pulumi.Output[str] | str]
)
```

* `universal` - Your defined *dorc* universal configuration model.
* `vpc_id` - The ID of your AWS VPC where the infrastructure will be deployed.
* `private_subnet_ids` - A list of AWS private subnet IDs to attach to the resources.
* `rAPId_config` - If integrating with rAPId specify your rAPId instance configuration here. See the [rAPId integration](/rapid_integration/#rapid-config) for further information.
* `additional_lambda_role_policy_arn` - By default, *dorc* creates a lambda policy that is sufficient to start with. However, if you require specific access to different services within your lambdas, you can create your own policy and pass the AWS ARN to *dorc*, which will attach it to its default policy.
* `additional_state_function_role_policy_arn` - Similar to the lambda policy, but attached to the default state machines policy.
* `additional_cloudevent_state_machine_trigger_role_policy_arn` - Similar to the lambda policy, but attached to the default CloudEvent trigger policy.

Please note that the types `pulumi.Output[str]`, `pulumi.Output[list[str]]` are part of the Pulumi framework, which is utilized by dorc for infrastructure deployment.
