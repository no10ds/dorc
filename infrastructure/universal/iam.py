import pulumi
import pulumi_aws as aws

from utils.abstracts import InfrastructureCreateBlock
from infrastructure.universal.config import Config


class CreateIAM(InfrastructureCreateBlock):
    def __init__(self, config: Config):
        self.config = config

    def apply(self):
        self.create_lambda_function_role()
        self.create_lambda_function_role_policy()
        self.create_state_function_role()
        self.create_state_function_role_policy()
        self.create_cloudevent_state_machine_trigger_role()
        self.create_cloudevent_state_machine_trigger_role_policy()

    def create_state_function_role(self):
        name = f"{self.config.project}-state-function-role"
        self.state_function_role = aws.iam.Role(
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
        )
        pulumi.export("state-function-role-arn", self.state_function_role.arn)

    def create_state_function_role_policy(self):
        name = f"{self.config.project}-state-function-role-policy"
        self.state_function_role_policy = aws.iam.RolePolicy(
            resource_name=name,
            name=name,
            role=self.state_function_role.id,
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
        )

    def create_lambda_function_role(self):
        name = f"{self.config.project}-lambda-role"
        self.lambda_function_role = aws.iam.Role(
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
        )
        pulumi.export("lambda-role-arn", self.lambda_function_role.arn)

    def create_lambda_function_role_policy(self):
        name = f"{self.config.project}-lambda-role-policy"
        self.lambda_function_role_policy = aws.iam.RolePolicy(
            resource_name=name,
            name=name,
            role=self.lambda_function_role.id,
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
        )

    def create_cloudevent_state_machine_trigger_role(self):
        name = f"{self.config.project}-cloudevent-state-machine-trigger-role"
        self.cloudevent_state_machine_trigger_role = aws.iam.Role(
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
        )
        pulumi.export(
            "cloudevent-state-machine-trigger-role-arn",
            self.cloudevent_state_machine_trigger_role.arn,
        )

    def create_cloudevent_state_machine_trigger_role_policy(self):
        name = f"{self.config.project}-cloudevent-state-machine-trigger-policy"
        self.cloudevent_state_machine_trigger_role_policy = aws.iam.RolePolicy(
            resource_name=name,
            name=name,
            role=self.cloudevent_state_machine_trigger_role.id,
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
        )
