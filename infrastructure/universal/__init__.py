import pulumi

from infrastructure.universal.core import (
    create_code_storage_bucket,
    create_cloudwatch_log_group,
    create_state_function_role,
    create_state_function_policy,
    create_lambda_role,
    create_lambda_policy
)

# TODO: Probably want to move this out of the __init__
class CreateUniversalPipelineInfrastructure():

    def __init__(self) -> None:
        # TODO: Pass in project configuration and perform validation
        pass

    def apply(self) -> None:
        # TODO: We want some way to return all of these resource blocks back from the class
        # probably set them as class variables and then create some getters
        create_code_storage_bucket("step-functions-code-storage")
        create_cloudwatch_log_group()

        self.state_function_role = create_state_function_role()
        self.state_function_policy = create_state_function_policy(self.state_function_role)

        self.lambda_role = create_lambda_role()
        self.lambda_policy = create_lambda_policy(self.lambda_role)

        pulumi.export("state_function_role_arn", self.state_function_role.arn)
        pulumi.export("lambda_role_arn", self.lambda_role.arn)