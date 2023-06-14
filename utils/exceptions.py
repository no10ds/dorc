class InvalidPipelineDefinitionException(Exception):
    pass


class EnvironmentRequiredException(Exception):
    pass


class PipelineDoesNotExistException(Exception):
    pass


class CannotFindEnvironmentVariableException(Exception):
    pass
