"""Chat routes."""

import time
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.security import get_current_user
from app.db.database import AuditLogDB, UserDB, get_db, utc_now
from app.schemas.chat import ChatQuery, ChatResponse
from app.services.chat import route_query

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/query", response_model=ChatResponse)
def chat_query(
    request: ChatQuery,
    current_user: Annotated[UserDB, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ChatResponse:
    started = time.perf_counter()
    session_id = request.session_id or str(uuid.uuid4())
    answer, tool, citations, warnings, confidence = route_query(request.query, current_user.role, db)
    execution_time_ms = round((time.perf_counter() - started) * 1000, 3)
    db.add(
        AuditLogDB(
            session_id=session_id,
            user_role=current_user.role,
            tool_used=tool,
            status="success" if tool != "access_control" else "rejected",
            timestamp=utc_now(),
        )
    )
    db.commit()
    return ChatResponse(
        answer=answer,
        citations=citations,
        warnings=warnings,
        confidence=confidence,
        tool_executed=tool,
        execution_time_ms=execution_time_ms,
    )
