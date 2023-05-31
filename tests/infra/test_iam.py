import pytest
import pulumi

from mock import patch, call, ANY
from infrastructure.infra.creator import CreateInfra
from infrastructure.infra.iam import CreateIamResource

from tests.utils import config


class TestCreateIamResource:
    @pytest.mark.usefixtures("mock_pulumi", "mock_pulumi_config")
    @pytest.fixture
    def infra_infrastructure_block(self, mock_pulumi, mock_pulumi_config):
        infra_infrastructure_block = CreateInfra(config)
        return infra_infrastructure_block

    @pytest.mark.usefixtures("infra_infrastructure_block")
    @pytest.fixture
    def iam_resource_block(
        self, infra_infrastructure_block: CreateInfra
    ) -> CreateIamResource:
        iam_resource_block = CreateIamResource(
            config=infra_infrastructure_block.config,
            aws_provider=infra_infrastructure_block.aws_provider,
            environment=infra_infrastructure_block.environment,
        )
        return iam_resource_block

    @pytest.mark.usefixtures("iam_resource_block")
    def test_instantiate_create_iam_resource(self, iam_resource_block):
        assert iam_resource_block.project == config.project

    @pytest.mark.usefixtures("iam_resource_block")
    @pulumi.runtime.test
    def test_iam_lambda_role_created(self, iam_resource_block: CreateIamResource):
        def check_lambda_role(args):
            name, tags = args
            assert name == "test-pipelines-test-lambda-role"
            assert tags == config.tags

        lambda_role = iam_resource_block.outputs.lambda_function_role
        return pulumi.Output.all(lambda_role.name, lambda_role.tags).apply(
            check_lambda_role
        )

    @pytest.mark.usefixtures("iam_resource_block")
    @pulumi.runtime.test
    def test_iam_state_function_role_created(
        self, iam_resource_block: CreateIamResource
    ):
        def check_state_function_role(args):
            name, tags = args
            assert name == "test-pipelines-test-state-function-role"
            assert tags == config.tags

        state_function_role = iam_resource_block.outputs.state_function_role
        return pulumi.Output.all(
            state_function_role.name, state_function_role.tags
        ).apply(check_state_function_role)

    @pytest.mark.usefixtures("iam_resource_block")
    @pulumi.runtime.test
    def test_iam_cloudevent_state_function_role_created(
        self, iam_resource_block: CreateIamResource
    ):
        def check_cloudevent_function_role(args):
            name, tags = args
            assert name == "test-pipelines-test-cloudevent-sm-trigger-role"
            assert tags == config.tags

        clouevent_state_function_role = (
            iam_resource_block.outputs.cloudevent_state_machine_trigger_role
        )
        return pulumi.Output.all(
            clouevent_state_function_role.name, clouevent_state_function_role.tags
        ).apply(check_cloudevent_function_role)

    @pytest.mark.usefixtures("iam_resource_block")
    @pulumi.runtime.test
    def test_iam_additional_lambda_role_policy_created(
        self, iam_resource_block: CreateIamResource
    ):
        iam_resource_block.config.additional_lambda_role_policy_arn = (
            "lambda_role_policy_arn"
        )
        additional_lambda_role_policy = (
            iam_resource_block.outputs.additional_lambda_role_policy
        )

        def check_additional_lambda_role_policy(args):
            policy_arn, role = args
            assert policy_arn == "lambda_role_policy_arn"
            assert role == "test-pipelines-test-lambda-role"

        return pulumi.Output.all(
            additional_lambda_role_policy.policy_arn, additional_lambda_role_policy.role
        ).apply(check_additional_lambda_role_policy)

    @pytest.mark.usefixtures("iam_resource_block")
    @pulumi.runtime.test
    def test_iam_additional_state_function_role_policy_created(
        self, iam_resource_block: CreateIamResource
    ):
        iam_resource_block.config.additional_state_function_role_policy_arn = (
            "state_function_role_policy_arn"
        )
        additional_state_function_role_policy = (
            iam_resource_block.outputs.additional_state_function_role_policy
        )

        def check_additional_state_function_role_policy(args):
            policy_arn, role = args
            assert policy_arn == "state_function_role_policy_arn"
            assert role == "test-pipelines-test-state-function-role"

        return pulumi.Output.all(
            additional_state_function_role_policy.policy_arn,
            additional_state_function_role_policy.role,
        ).apply(check_additional_state_function_role_policy)

    @pytest.mark.usefixtures("iam_resource_block")
    @pulumi.runtime.test
    def test_iam_additional_cloudevent_state_machine_trigger_role_policy_created(
        self, iam_resource_block: CreateIamResource
    ):
        iam_resource_block.config.additional_cloudevent_state_machine_trigger_role_policy_arn = (
            "cloudevent_state_machine_trigger_role_policy_arn"
        )
        additional_cloudevent_state_machine_trigger_role_policy = (
            iam_resource_block.outputs.additional_cloudevent_state_machine_trigger_role_policy
        )

        def check_additional_cloudevent_state_machine_trigger_role_policy(args):
            policy_arn, role = args
            assert policy_arn == "cloudevent_state_machine_trigger_role_policy_arn"
            assert role == "test-pipelines-test-state-function-role"

        return pulumi.Output.all(
            additional_cloudevent_state_machine_trigger_role_policy.policy_arn,
            additional_cloudevent_state_machine_trigger_role_policy.role,
        ).apply(check_additional_cloudevent_state_machine_trigger_role_policy)
