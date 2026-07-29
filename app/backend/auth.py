from __future__ import annotations

from fastapi import HTTPException, Request
from databricks.sdk import WorkspaceClient

_sp_client: WorkspaceClient | None = None


def sp_client() -> WorkspaceClient:
    global _sp_client
    if _sp_client is None:
        _sp_client = WorkspaceClient()
    return _sp_client


def obo_client(request: Request) -> WorkspaceClient:
    token = request.headers.get("X-Forwarded-Access-Token")
    if not token:
        raise HTTPException(status_code=401, detail="Missing X-Forwarded-Access-Token.")
    return WorkspaceClient(token=token, auth_type="pat")
