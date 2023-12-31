from typing import Any, Optional

import pulumi

from pulumi import Output
from pulumi.dynamic.dynamic import (
    CreateResult,
    UpdateResult,
    ResourceProvider,
    Resource,
)
from rapid import Rapid
from rapid import RapidAuth
from rapid.exceptions import (
    InvalidPermissionsException,
    SubjectAlreadyExistsException,
    SubjectNotFoundException,
)


def create_rapid_connection(props: dict) -> Rapid:
    client_id = props["dorc_client_id"]
    client_secret = props["dorc_client_secret"]
    url = props["rapid_url"]
    return Rapid(auth=RapidAuth(client_id, client_secret, url))


class RapidClientProvider(ResourceProvider):
    def create(self, props) -> CreateResult:
        rapid = create_rapid_connection(props)
        try:
            client = self.create_client(
                rapid, props["client_name"], props["permissions"]
            )
            return CreateResult(
                client["client_id"],
                {
                    "client_id": client["client_id"],
                    "client_secret": client["client_secret"],
                    **props,
                },
            )
        except SubjectAlreadyExistsException as ex:
            raise ValueError(
                "Client already exists, try a different name or remove it from rAPId"
            ) from ex
        except InvalidPermissionsException as ex:
            raise ValueError("Invalid rAPId domain or layer configuration") from ex

    def update(self, _id: str, _olds: Any, _news: Any) -> UpdateResult:
        rapid = create_rapid_connection(_news)
        if _olds.get("permissions") != _news.get("permissions"):
            self.update_client_permissions(rapid, _id, _news["permissions"])

        return UpdateResult({**_news})

    def delete(self, _id: str, _props: Any) -> None:
        rapid = create_rapid_connection(_props)
        self.delete_client(rapid, _id)

    def delete_client(self, rapid: Rapid, client_id: str):
        try:
            rapid.delete_client(client_id)
        except SubjectNotFoundException:
            pass

    def create_client(
        self, rapid: Rapid, client_name: str, permissions: list[str]
    ) -> dict:
        client = rapid.create_client(client_name, permissions)
        return client

    def update_client_permissions(
        self, rapid: Rapid, client_id: str, permissions: list[str]
    ) -> None:
        try:
            rapid.update_subject_permissions(client_id, permissions)
        except InvalidPermissionsException as ex:
            raise ValueError("Invalid rAPId domain or layer configuration") from ex


class RapidClient(Resource):
    id: Output[str]  # Acts as the client_id to match the UserPoolClient output
    client_secret: Output[str]
    dorc_client_id: Output[str]
    dorc_client_secret: Output[str]

    def __init__(
        self,
        resource_name: str,
        dorc_client_id: str,
        dorc_client_secret: str,
        rapid_url: str,
        client_name: str,
        permissions: list[str],
        opts: Optional[pulumi.ResourceOptions] = None,
    ):
        args = {
            "dorc_client_id": dorc_client_id,
            "dorc_client_secret": dorc_client_secret,
            "rapid_url": rapid_url,
            "client_name": client_name,
            "permissions": permissions,
            "client_secret": None,
        }
        super().__init__(RapidClientProvider(), resource_name, args, opts)
