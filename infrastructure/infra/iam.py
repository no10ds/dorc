import pulumi
import pulumi_aws as aws

from pulumi import ResourceOptions, Output
from pulumi_aws import Provider
from pulumi_aws.iam import Role
from utils.abstracts import CreateResourceBlock
from utils.config import Config
from utils.constants import (
    STATE_FUNCTION_ROLE_ARN,
    LAMBDA_ROLE_ARN,
    CLOUDEVENT_STATE_MACHINE_TRIGGER_ROLE_ARN,
)


class CreateIamResource(CreateResourceBlock):
    class Output(CreateResourceBlock.Output):
        lambda_function_role: Role
        state_function_role: Role
        cloudevent_state_machine_trigger_role: Role

    def __init__(
        self, config: Config, aws_provider: Provider, environment: str
    ) -> None:
        super().__init__(config, aws_provider, environment)
        self.project = self.config.project

    def apply(self) -> Output:
        lambda_function_role = self.create_lambda_function_role()
        self.create_lambda_function_role_policy(lambda_function_role.id)

        state_function_role = self.create_state_function_role()
        self.create_state_function_role_policy(state_function_role.id)

        cloudevent_state_machine_trigger_role = (
            self.create_cloudevent_state_machine_trigger_role()
        )
        self.create_cloudevent_state_machine_trigger_role_policy(
            cloudevent_state_machine_trigger_role.id
        )

        if self.config.additional_lambda_role_policy_arn is not None:
            self.apply_additional_lambda_role_policy()

        if self.config.additional_state_function_role_policy_arn is not None:
            self.apply_additional_state_function_role_policy()

        if (
            self.config.additional_cloudevent_state_machine_trigger_role_policy_arn
            is not None
        ):
            self.apply_additional_cloudevent_state_machine_trigger_role_policy()

        output = self.Output(
            lambda_function_role=lambda_function_role,
            state_function_role=state_function_role,
            cloudevent_state_machine_trigger_role=cloudevent_state_machine_trigger_role,
        )

        return output

    def export(self):
        pulumi.export(LAMBDA_ROLE_ARN, self.outputs.lambda_function_role.arn)
        pulumi.export(STATE_FUNCTION_ROLE_ARN, self.outputs.state_function_role.arn)
        pulumi.export(
            CLOUDEVENT_STATE_MACHINE_TRIGGER_ROLE_ARN,
            self.outputs.cloudevent_state_machine_trigger_role.arn,
        )

    def create_lambda_function_role(self):
        name = f"{self.project}-{self.environment}-lambda-role"
        return aws.iam.Role(
            resource_name=name,
            name=name,
            assume_role_policy="""{
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": "sts:AssumeRole",
                        "Principal": {
                            "Service": "lambda.amazonaws.com"
                        },
                        "Effect": "Allow",
                        "Sid": ""
                    }
                ]
            }""",
            opts=ResourceOptions(provider=self.aws_provider),
        )

    def create_lambda_function_role_policy(self, lambda_function_role_id):
        name = f"{self.project}-{self.environment}-lambda-role-policy"
        return aws.iam.RolePolicy(
            resource_name=name,
            name=name,
            role=lambda_function_role_id,
            policy="""{
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": [
                                "logs:CreateLogGroup",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents"
                            ],
                            "Resource": "arn:aws:logs:*:*:*"
                        },
                        {
                            "Effect": "Allow",
                            "Action": [
                                "ec2:CreateNetworkInterface",
                                "ec2:DescribeNetworkInterfaces",
                                "ec2:DeleteNetworkInterface"
                            ],
                            "Resource": "*"
                        }
                    ]
                }""",
            opts=ResourceOptions(provider=self.aws_provider),
        )

    def create_state_function_role(self):
        name = f"{self.project}-{self.environment}-state-function-role"
        return aws.iam.Role(
            resource_name=name,
            name=name,
            assume_role_policy="""{
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {
                                "Service": "states.amazonaws.com"
                            },
                            "Action": "sts:AssumeRole"
                        }
                    ]
                }""",
            opts=ResourceOptions(provider=self.aws_provider),
        )

    def create_state_function_role_policy(self, state_function_role_id):
        name = f"{self.project}-{self.environment}-state-function-role-policy"
        return aws.iam.RolePolicy(
            resource_name=name,
            name=name,
            role=state_function_role_id,
            policy="""{
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "lambda:InvokeFunction"
                        ],
                        "Resource": "*"
                    },
                    {
                        "Effect": "Allow",
                        "Action": [
                            "states:DescribeExecution",
                            "states:StopExecution",
                            "states:StartExecution",
                            "events:PutTargets",
                            "events:PutRule",
                            "events:DescribeRule"
                        ],
                        "Resource": "*"
                    }
                ]
            }""",
            opts=ResourceOptions(provider=self.aws_provider),
        )

    def create_cloudevent_state_machine_trigger_role(self):
        name = f"{self.project}-{self.environment}-cloudevent-sm-trigger-role"
        return aws.iam.Role(
            resource_name=name,
            name=name,
            assume_role_policy="""{
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": "sts:AssumeRole",
                        "Principal": {
                            "Service": "events.amazonaws.com"
                        },
                        "Effect": "Allow",
                        "Sid": ""
                    }
                ]
            }""",
            opts=ResourceOptions(provider=self.aws_provider),
        )

    def create_cloudevent_state_machine_trigger_role_policy(
        self, cloudevent_state_machine_trigger_role_id
    ):
        name = f"{self.project}-{self.environment}-cloudevent-sm-trigger-policy"
        return aws.iam.RolePolicy(
            resource_name=name,
            name=name,
            role=cloudevent_state_machine_trigger_role_id,
            policy="""{
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Action": [
                        "states:StartExecution"
                    ],
                    "Resource": "*"
                }]
            }""",
            opts=ResourceOptions(provider=self.aws_provider),
        )

    def apply_additional_lambda_role_policy(self):
        name = f"{self.project}-{self.environment}-additional-lambda-role-policy-attachment"
        policy_arn = self.to_output(self.config.additional_lambda_role_policy_arn)
        aws.iam.RolePolicyAttachment(
            resource_name=name,
            policy_arn=policy_arn,
            role=self.lambda_function_role.name,
            opts=ResourceOptions(provider=self.aws_provider),
        )

    def apply_additional_state_function_role_policy(self):
        name = f"{self.project}-{self.environment}-additional-sf-role-policy-attachment"
        policy_arn = self.to_output(
            self.config.additional_state_function_role_policy_arn
        )
        aws.iam.RolePolicyAttachment(
            resource_name=name,
            policy_arn=policy_arn,
            role=self.state_function_role.name,
            opts=ResourceOptions(provider=self.aws_provider),
        )

    def apply_additional_cloudevent_state_machine_trigger_role_policy(self):
        name = f"{self.project}-{self.environment}-additional-cloudevent-sm-trigger-role-policy-attachment"
        policy_arn = self.to_output(
            self.config.additional_cloudevent_state_machine_trigger_role_policy_arn
        )
        aws.iam.RolePolicyAttachment(
            resource_name=name,
            policy_arn=policy_arn,
            role=self.state_function_role.name,
            opts=ResourceOptions(provider=self.aws_provider),
        )

    def to_output(self, v):
        return v if isinstance(v, Output) else Output.from_input(v)
