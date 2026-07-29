from __future__ import annotations

import os

from databricks.sdk.core import Config, oauth_service_principal


def get_bearer() -> str:
    host = os.environ["DATABRICKS_HOST"]
    client_id = os.environ["DATABRICKS_CLIENT_ID"]
    client_secret = os.environ["DATABRICKS_CLIENT_SECRET"]

    cfg = Config(host=host, client_id=client_id, client_secret=client_secret)
    credentials = oauth_service_principal(cfg)
    if credentials is None:
        raise RuntimeError("Failed to obtain M2M OAuth credentials for the service principal")
    token = credentials().get("Authorization", "").removeprefix("Bearer ")
    if not token:
        raise RuntimeError("No access_token returned from client_credentials grant")
    return token
