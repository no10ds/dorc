class InvalidPipelineDefinitionException(Exception):
    pass


class InvalidConfigDefinitionException(Exception):
    pass


class EnvironmentRequiredException(Exception):
    pass


class PipelineDoesNotExistException(Exception):
    pass


class CannotFindEnvironmentVariableException(Exception):
    pass
