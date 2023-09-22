from typing import Type

from infrastructure.core.models.definition import PipelineDefinition, rAPIdTrigger
from utils.config import rAPIdConfig
from utils.exceptions import InvalidConfigDefinitionException


def validate_rapid_trigger(
    pipeline_definition: Type[PipelineDefinition], rapid_config: Type[rAPIdConfig]
):
    """
    Need to handle 2 different options

    1. They pass a client key into the pipeline definition
        - we expect a rAPId prefix
        - automatically fetch the client secret (probably want to raise an issue if it doesn't load)
    2. They don't pass a client key into the pipeline definition
        - we expect a rAPId prefix
        - we need a rAPId user pool id
        - we need a valid dorc rAPId client
        - automatically create a client key using the user pool id

    Then we pass the client id and client secret into the environment variable of the lambda function
    """
    trigger = pipeline_definition.trigger
    is_rapid_trigger = isinstance(trigger, rAPIdTrigger)

    if is_rapid_trigger:
        # Require a valid rAPId config
        if rapid_config is None:
            raise InvalidConfigDefinitionException(
                "Passing a rAPId trigger requires a rAPId config to be set."
            )

        # Require a valid dorc rAPId client to be present if they aren't passing specific clients
        if trigger.client_key is None and rapid_config.dorc_rapid_client_id is None:
            raise InvalidConfigDefinitionException(
                "Using rAPId without passing a specific client key requires a dorc rAPId client to be present."
            )
