import pulumi

from infrastructure.universal.core import (
    create_code_storage_bucket,
    create_cloudwatch_log_group,
    create_state_function_role,
    create_state_function_policy,
    create_lambda_role,
    create_lambda_policy
)

class CreateUniversalPipelineInfrastructure():

    def __init__(self) -> None:
        # TODO: Pass in project configuration and perform validation
        pass

    def apply(self) -> None:
        create_code_storage_bucket("step-functions-code-storage")
        create_cloudwatch_log_group()

        self.state_function_role = create_state_function_role()
        self.state_function_policy = create_state_function_policy(self.state_function_role)

        self.lambda_role = create_lambda_role()
        self.lambda_policy = create_lambda_policy(self.lambda_role)

        self.export()

    def export(self) -> None:
        pulumi.export("state_function_role_arn", self.state_function_role.arn)
        pulumi.export("lambda_role_arn", self.lambda_role.arn)