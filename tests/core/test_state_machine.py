import json
from mock import MagicMock
import pytest

from infrastructure.core.state_machine import CreatePipelineStateMachine
from infrastructure.core.creator import CreatePipeline
from infrastructure.core.models.definition import (
    PipelineDefinition,
    NextFunction,
    NextFunctionTypes,
    Function,
)
from utils.exceptions import PipelineDoesNotExistException


class TestCreateStateMachine:
    @pytest.mark.usefixtures(
        "mock_pulumi", "mock_pulumi_config", "config", "pipeline_definition"
    )
    @pytest.fixture
    def pipeline_infrastructure_block(
        self, mock_pulumi, mock_pulumi_config, config, pipeline_definition
    ):
        pipeline_infrastructure_block = CreatePipeline(config, pipeline_definition)
        return pipeline_infrastructure_block

    @pytest.mark.usefixtures("pipeline_infrastructure_block")
    @pytest.fixture
    def state_machine_resource_block(
        self, pipeline_infrastructure_block: CreatePipeline
    ):
        mock_step_function_client = MagicMock()
        mock_step_function_client.list_state_machines.return_value = {
            "stateMachines": [
                {
                    "name": "test_pipeline_test_pipeline",
                    "stateMachineArn": "test_pipeline_arn",
                }
            ]
        }

        state_machine_resource_block = CreatePipelineStateMachine(
            pipeline_infrastructure_block.config,
            pipeline_infrastructure_block.aws_provider,
            pipeline_infrastructure_block.environment,
            "test-pipeline",
            pipeline_infrastructure_block.pipeline_definition,
            {},
            "test:state-machine:role",
            mock_step_function_client,
        )
        return state_machine_resource_block

    @pytest.mark.usefixtures("state_machine_resource_block", "config")
    def test_instantiate_create_state_machine_resource(
        self, state_machine_resource_block, config
    ):
        assert state_machine_resource_block.project == config.project

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
            "Next": "test-next-function",
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
        name_to_arn_map = {
            "lambda-1": "test-lambda-1-arn",
            "lambda-2": "test-lambda-2-arn",
            "lambda-3": "test-lambda-3-arn",
        }

        state_machine_resource_block.pipeline_definition = PipelineDefinition(
            file_path=__file__,
            description="Test pipeline",
            functions=[
                Function(
                    name="lambda-1",
                    next_function=NextFunction(name="lambda-2"),
                ),
                Function(
                    name="lambda-2",
                    next_function=NextFunction(name="lambda-3"),
                ),
                Function(
                    name="lambda-3",
                ),
            ],
        )
        expected = {
            "Comment": "Test pipeline",
            "StartAt": "lambda-1",
            "States": {
                "lambda-1": {
                    "Type": "Task",
                    "Resource": "test-lambda-1-arn",
                    "Next": "lambda-2",
                },
                "lambda-2": {
                    "Type": "Task",
                    "Resource": "test-lambda-2-arn",
                    "Next": "lambda-3",
                },
                "lambda-3": {
                    "Type": "Task",
                    "Resource": "test-lambda-3-arn",
                    "End": True,
                },
            },
        }

        res = state_machine_resource_block.create_state_machine_definition(
            name_to_arn_map
        )
        assert json.loads(res) == expected

    @pytest.mark.usefixtures("state_machine_resource_block")
    def test_create_state_machine_definition_next_function_as_pipeline(
        self, state_machine_resource_block
    ):
        state_machine_resource_block.fetch_step_function_arn_from_name = MagicMock(
            return_value="next-function-arn"
        )

        name_to_arn_map = {
            "lambda-1": "lambda-1-arn",
            "lambda-2": "lambda-2-arn",
        }
        state_machine_resource_block.pipeline_definition = PipelineDefinition(
            file_path=__file__,
            description="Test pipeline",
            functions=[
                Function(
                    name="lambda-1",
                    next_function=NextFunction(name="lambda-2"),
                ),
                Function(
                    name="lambda-2",
                    next_function=NextFunction(
                        name="test-pipeline", type=NextFunctionTypes.PIPELINE
                    ),
                ),
            ],
        )

        expected = {
            "Comment": "Test pipeline",
            "StartAt": "lambda-1",
            "States": {
                "lambda-1": {
                    "Type": "Task",
                    "Resource": "lambda-1-arn",
                    "Next": "lambda-2",
                },
                "lambda-2": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::states:startExecution.sync:2",
                    "Parameters": {"StateMachineArn": "next-function-arn"},
                    "End": True,
                },
            },
        }

        res = state_machine_resource_block.create_state_machine_definition(
            name_to_arn_map
        )
        assert json.loads(res) == expected

    @pytest.mark.usefixtures("state_machine_resource_block")
    def test_fetch_step_function_arn_from_name(self, state_machine_resource_block):
        with pytest.raises(PipelineDoesNotExistException):
            state_machine_resource_block.fetch_step_function_arn_from_name(
                "non_existent_function"
            )
