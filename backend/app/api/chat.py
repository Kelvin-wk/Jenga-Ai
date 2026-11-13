"""Chat routes."""

import json
import time
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.api.conversations import _owner_or_404, get_or_create_current_conversation
from app.auth.security import get_current_user
from app.db.database import (
    AuditLogDB,
    ConversationMessageDB,
    MediaContentDB,
    MediaDB,
    UserDB,
    get_db,
    utc_now,
)
from app.schemas.chat import Citation, ChatQuery, ChatResponse
from app.services.chat import route_query
from app.services.media import load_chat_attachments

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/query", response_model=ChatResponse)
def chat_query(
    request: ChatQuery,
    current_user: Annotated[UserDB, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ChatResponse:
    started = time.perf_counter()
    conversation = (
        _owner_or_404(request.conversation_id, current_user, db)
        if request.conversation_id
        else get_or_create_current_conversation(current_user, db)
    )
    if conversation.status != "active":
        raise HTTPException(status_code=409, detail="Conversation is finished")

    uploaded_media: list[MediaDB] = []
    if request.media_ids:
        if len(set(request.media_ids)) != len(request.media_ids):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Each attachment may only be included once.",
            )
        uploaded_media = db.scalars(
            select(MediaDB).where(
                MediaDB.id.in_(request.media_ids),
                MediaDB.user_id == current_user.id,
                MediaDB.active.is_(True),
            )
        ).all()
        if len(uploaded_media) != len(request.media_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more attachments were not found.",
            )
        if not request.allow_external_processing:
            raise HTTPException(
                status_code=status.HTTP_428_PRECONDITION_REQUIRED,
                detail="Confirm you are allowed to send these attachments to the configured AI service.",
            )
    attachments = load_chat_attachments(request.media_ids, current_user.id, db)
    request_text = request.text or request.query
    if not request_text and not attachments:
        raise HTTPException(status_code=422, detail="Enter a message or attach a file.")
    text = (
        request_text.strip()
        if request_text and request_text.strip()
        else "Please analyze the attached file(s)."
    )
    answer, tool, citation_names, warnings, confidence = route_query(
        text,
        current_user.role,
        db,
        attachments=attachments,
    )
    execution_time_ms = round((time.perf_counter() - started) * 1000, 3)
    now = utc_now()
    attachment_names = [attachment.filename for attachment in attachments]
    if request.media_ids:
        for media in uploaded_media:
            media.active = False
        db.execute(
            delete(MediaContentDB).where(
                MediaContentDB.media_id.in_(request.media_ids)
            )
        )
    db.add(
        AuditLogDB(
            session_id=conversation.id,
            user_role=current_user.role,
            tool_used=tool,
            status="success" if tool != "access_control" else "rejected",
            timestamp=now,
        )
    )
    db.add_all(
        [
            ConversationMessageDB(
                conversation_id=conversation.id,
                role="user",
                content=text,
                metadata_json=json.dumps(
                    {
                        "attachments": attachment_names,
                        "external_processing_approved": request.allow_external_processing,
                    }
                ),
                created_at=now,
            ),
            ConversationMessageDB(
                conversation_id=conversation.id,
                role="assistant",
                content=answer,
                metadata_json=json.dumps(
                    {
                        "citations": [
                            {"source_id": name} for name in citation_names
                        ],
                        "warnings": warnings,
                        "confidence": confidence,
                        "tool_executed": tool,
                        "attachments": attachment_names,
                    }
                ),
                created_at=now,
            ),
        ]
    )
    db.commit()
    return ChatResponse(
        answer=answer,
        citations=[Citation(source_id=citation) for citation in citation_names],
        warnings=warnings,
        confidence=confidence,
        tool_executed=tool,
        execution_time_ms=execution_time_ms,
        request_id=str(uuid.uuid4()),
        conversation_id=conversation.id,
        tool_trace_id=conversation.id,
        latency_ms=execution_time_ms,
        needs_human_review=tool == "safety_notice",
    )
