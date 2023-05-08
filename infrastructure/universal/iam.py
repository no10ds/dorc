import pulumi_aws as aws


def create_state_function_role():
    return aws.iam.Role(
        "state-function-role",
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


def create_state_function_policy(state_function_role):
    return aws.iam.RolePolicy(
        "state-function-role-policy",
        role=state_function_role.id,
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


def create_lambda_role():
    return aws.iam.Role(
        "lambda-role",
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


def create_lambda_policy(lambda_role):
    return aws.iam.RolePolicy(
        "lambda-role-policy",
        role=lambda_role.id,
        policy="""{
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Resource": "arn:aws:logs:*:*:*"
            }]
        }""",
    )


def create_cloudevent_state_machine_trigger_role():
    return aws.iam.Role(
        "cloudevent_state_machine_trigger_role",
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
