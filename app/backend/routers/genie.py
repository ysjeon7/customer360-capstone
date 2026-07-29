from __future__ import annotations

import os

from fastapi import APIRouter, Request
from pydantic import BaseModel

from ..auth import obo_client

router = APIRouter(prefix="/api/genie", tags=["genie"])

GENIE_SPACE_ID = os.environ["GENIE_SPACE_ID"]


class MessageIn(BaseModel):
    content: str


def _serialize(msg) -> dict:
    out = {
        "conversation_id": msg.conversation_id,
        "message_id": msg.message_id or msg.id,
        "status": str(msg.status) if msg.status else None,
        "content": msg.content,
        "attachments": [],
    }
    for att in msg.attachments or []:
        out["attachments"].append({
            "attachment_id": att.attachment_id,
            "text": att.text.content if att.text else None,
            "has_query": att.query is not None,
            "query_description": att.query.description if att.query else None,
        })
    return out


@router.post("/conversations")
def start_conversation(body: MessageIn, request: Request):
    w = obo_client(request)
    wait = w.genie.start_conversation(space_id=GENIE_SPACE_ID, content=body.content)
    return _serialize(wait.response)


@router.post("/conversations/{conversation_id}/messages")
def create_message(conversation_id: str, body: MessageIn, request: Request):
    w = obo_client(request)
    wait = w.genie.create_message(
        space_id=GENIE_SPACE_ID,
        conversation_id=conversation_id,
        content=body.content,
    )
    return _serialize(wait.response)


@router.get("/conversations/{conversation_id}/messages/{message_id}")
def get_message(conversation_id: str, message_id: str, request: Request):
    w = obo_client(request)
    msg = w.genie.get_message(
        space_id=GENIE_SPACE_ID,
        conversation_id=conversation_id,
        message_id=message_id,
    )
    result = _serialize(msg)

    for att in msg.attachments or []:
        if att.query is not None:
            qr = w.genie.get_message_attachment_query_result(
                space_id=GENIE_SPACE_ID,
                conversation_id=conversation_id,
                message_id=message_id,
                attachment_id=att.attachment_id,
            )
            sr = qr.statement_response
            if sr and sr.result and sr.result.data_array:
                cols = [c.name for c in sr.manifest.schema.columns]
                result["query_result"] = {
                    "columns": cols,
                    "rows": sr.result.data_array,
                }
            break

    return result
