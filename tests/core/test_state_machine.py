import json
import pytest
import pulumi

from pulumi_aws.lambda_ import Function as AwsFunction
from infrastructure.core.state_machine import CreatePipelineStateMachine
from infrastructure.core.creator import CreatePipeline
from infrastructure.core.models.definition import (
    PipelineDefinition,
    NextFunction,
    NextFunctionTypes,
    Function,
)

from tests.utils import config, pipeline_definition


class TestCreateStateMachine:
    @pytest.mark.usefixtures("mock_pulumi", "mock_pulumi_config")
    @pytest.fixture
    def pipeline_infrastructure_block(self, mock_pulumi, mock_pulumi_config):
        pipeline_infrastructure_block = CreatePipeline(config, pipeline_definition)
        yield pipeline_infrastructure_block

    @pytest.mark.usefixtures("pipeline_infrastructure_block")
    @pytest.fixture
    def state_machine_resource_block(
        self, pipeline_infrastructure_block: CreatePipeline
    ):
        state_machine_resource_block = CreatePipelineStateMachine(
            pipeline_infrastructure_block.config,
            pipeline_infrastructure_block.aws_provider,
            pipeline_infrastructure_block.environment,
            "test-pipeline",
            pipeline_infrastructure_block.pipeline_definition,
            {},
            "test:state-machine:role",
        )
        yield state_machine_resource_block

    @pytest.mark.usefixtures("state_machine_resource_block")
    def test_instantiate_create_state_machine_resource(
        self, state_machine_resource_block
    ):
        assert state_machine_resource_block.project == config.project

    @pytest.mark.usefixtures("state_machine_resource_block")
    def test_create_function_name(
        self, state_machine_resource_block: CreatePipelineStateMachine
    ):
        assert (
            state_machine_resource_block.create_function_name("function")
            == "test_pipeline_function"
        )

    @pytest.mark.usefixtures("state_machine_resource_block")
    def test_create_lambda_next_trigger_state(
        self, state_machine_resource_block: CreatePipelineStateMachine
    ):
        arn = "some:test:arn"
        next_function_name = "test-next-function"
        state_map = state_machine_resource_block.create_lambda_next_trigger_state(
            arn, next_function_name
        )
        assert state_map == {
            "Type": "Task",
            "Resource": "some:test:arn",
            "Next": "test_pipeline_test_next_function",
        }

    @pytest.mark.usefixtures("state_machine_resource_block")
    def test_create_lambda_next_trigger_state_termination(
        self, state_machine_resource_block: CreatePipelineStateMachine
    ):
        arn = "some:test:arn"
        next_function_name = None
        state_map = state_machine_resource_block.create_lambda_next_trigger_state(
            arn, next_function_name
        )
        assert state_map == {"Type": "Task", "Resource": "some:test:arn", "End": True}

    @pytest.mark.usefixtures("state_machine_resource_block")
    def test_create_state_machine_definition(
        self, state_machine_resource_block: CreatePipelineStateMachine
    ):
        state_machine_resource_block.lambdas_dict = {
            "test_pipeline_test_lambda_1": "",
            "test_pipeline_test_lambda_2": "",
            "test_pipeline_test_lambda_3": "",
        }
        state_machine_resource_block.pipeline_definition = PipelineDefinition(
            file_path=__file__,
            description="Test pipeline",
            functions=[
                Function(
                    name="test-lambda-1",
                    next_function=NextFunction(name="test-lambda-2"),
                ),
                Function(
                    name="test-lambda-2",
                    next_function=NextFunction(name="test-lambda-3"),
                ),
                Function(
                    name="test-lambda-3",
                ),
            ],
        )
        arns = [["test:lambda-1:arn", "test:lambda-2:arn", "test:lambda-3:arn"]]
        definition = state_machine_resource_block.create_state_machine_definition(arns)
        assert json.loads(definition) == {
            "Comment": "Test pipeline",
            "StartAt": "test_pipeline_test_lambda_1",
            "States": {
                "test_pipeline_test_lambda_1": {
                    "Type": "Task",
                    "Resource": "test:lambda-1:arn",
                    "Next": "test_pipeline_test_lambda_2",
                },
                "test_pipeline_test_lambda_2": {
                    "Type": "Task",
                    "Resource": "test:lambda-2:arn",
                    "Next": "test_pipeline_test_lambda_3",
                },
                "test_pipeline_test_lambda_3": {
                    "Type": "Task",
                    "Resource": "test:lambda-3:arn",
                    "End": True,
                },
            },
        }

    @pytest.mark.usefixtures("state_machine_resource_block")
    def test_create_state_machine_definition_next_function_as_pipeline(
        self, state_machine_resource_block
    ):
        state_machine_resource_block.lambdas_dict = {
            "test_pipeline_test_lambda_1": "",
            "test_pipeline_test_lambda_2": "",
            "test_pipeline_test_pipeline": "",
        }

        state_machine_resource_block.pipeline_definition = PipelineDefinition(
            file_path=__file__,
            description="Test pipeline",
            functions=[
                Function(
                    name="test-lambda-1",
                    next_function=NextFunction(name="test-lambda-2"),
                ),
                Function(
                    name="test-lambda-2",
                    next_function=NextFunction(
                        name="test-pipeline", type=NextFunctionTypes.PIPELINE
                    ),
                ),
            ],
        )
        arns = [["test:lambda-1:arn", "test:lambda-2:arn", "test:pipeline:arn"]]
        definition = state_machine_resource_block.create_state_machine_definition(arns)
        assert json.loads(definition) == {
            "Comment": "Test pipeline",
            "StartAt": "test_pipeline_test_lambda_1",
            "States": {
                "test_pipeline_test_lambda_1": {
                    "Type": "Task",
                    "Resource": "test:lambda-1:arn",
                    "Next": "test_pipeline_test_lambda_2",
                },
                "test_pipeline_test_lambda_2": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::states:startExecution.sync:2",
                    "Parameters": {"StateMachineArn": "test-pipeline"},
                    "End": True,
                },
            },
        }

    @pytest.mark.usefixtures("state_machine_resource_block")
    @pulumi.runtime.test
    def test_create_state_machine(
        self, state_machine_resource_block: CreatePipelineStateMachine
    ):
        def check_state_function(args):
            definition = args[0]
            assert json.loads(definition) == {
                "Comment": "Test pipeline",
                "StartAt": "test_pipeline_test_lambda_1",
                "States": {
                    "test_pipeline_test_lambda_1": {
                        "Type": "Task",
                        "Resource": None,
                        "Next": "test_pipeline_test_lambda_2",
                    },
                    "test_pipeline_test_lambda_2": {
                        "Type": "Task",
                        "Resource": None,
                        "Next": "test_pipeline_test_lambda_3",
                    },
                    "test_pipeline_test_lambda_3": {
                        "Type": "Task",
                        "Resource": None,
                        "End": True,
                    },
                },
            }

        state_machine_resource_block.lambdas_dict = {
            "test_pipeline_test_lambda_1": AwsFunction(
                resource_name="test:lambda:1", name="test-lambda-1", role="role"
            ),
            "test_pipeline_test_lambda_2": AwsFunction(
                resource_name="test:lambda:1", name="test-lambda-2", role="role"
            ),
            "test_pipeline_test_lambda_3": AwsFunction(
                resource_name="test:lambda:1", name="test-lambda-3", role="role"
            ),
        }

        state_machine_resource_block.pipeline_definition = PipelineDefinition(
            file_path=__file__,
            description="Test pipeline",
            functions=[
                Function(
                    name="test-lambda-1",
                    next_function=NextFunction(name="test-lambda-2"),
                ),
                Function(
                    name="test-lambda-2",
                    next_function=NextFunction(name="test-lambda-3"),
                ),
                Function(
                    name="test-lambda-3",
                ),
            ],
        )

        return pulumi.Output.all(
            state_machine_resource_block.outputs.state_machine.definition
        ).apply(check_state_function)

    @pytest.mark.usefixtures("state_machine_resource_block")
    @pulumi.runtime.test
    def test_create_state_machine_next_function_as_pipeline(
        self, state_machine_resource_block
    ):
        def check_state_function(args):
            definition = args[0]
            assert json.loads(definition) == {
                "Comment": "Test pipeline",
                "StartAt": "test_pipeline_test_lambda_1",
                "States": {
                    "test_pipeline_test_lambda_1": {
                        "Type": "Task",
                        "Resource": None,
                        "Next": "test_pipeline_test_lambda_2",
                    },
                    "test_pipeline_test_lambda_2": {
                        "Type": "Task",
                        "Resource": "arn:aws:states:::states:startExecution.sync:2",
                        "Parameters": {"StateMachineArn": "test-pipeline"},
                        "End": True,
                    },
                },
            }

        state_machine_resource_block.lambdas_dict = {
            "test_pipeline_test_lambda_1": AwsFunction(
                resource_name="test:lambda:1", name="test-lambda-1", role="role"
            ),
            "test_pipeline_test_lambda_2": AwsFunction(
                resource_name="test:lambda:1", name="test-lambda-2", role="role"
            ),
        }
        state_machine_resource_block.pipeline_definition = PipelineDefinition(
            file_path=__file__,
            description="Test pipeline",
            functions=[
                Function(
                    name="test-lambda-1",
                    next_function=NextFunction(name="test-lambda-2"),
                ),
                Function(
                    name="test-lambda-2",
                    next_function=NextFunction(
                        name="test-pipeline", type=NextFunctionTypes.PIPELINE
                    ),
                ),
            ],
        )

        return pulumi.Output.all(
            state_machine_resource_block.outputs.state_machine.definition
        ).apply(check_state_function)
