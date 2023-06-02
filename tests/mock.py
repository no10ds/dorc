from pydantic import BaseModel  # pylint: disable=no-name-in-module


class MockedEcrAuthentication(BaseModel):
    password: str
    user_name: str
