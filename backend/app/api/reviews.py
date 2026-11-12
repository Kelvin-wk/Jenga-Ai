"""Human review escalation routes."""

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.security import get_current_user
from app.db.database import ConversationDB, ReviewRequestDB, UserDB, get_db
from app.schemas.catalogue import ReviewRequest

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("")
def submit_review(
    payload: ReviewRequest,
    current_user: Annotated[UserDB, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    conversation = db.scalar(
        select(ConversationDB).where(
            ConversationDB.id == payload.conversation_id,
            ConversationDB.user_id == current_user.id,
        )
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    review = ReviewRequestDB(
        id=f"review_{uuid.uuid4().hex}",
        conversation_id=conversation.id,
        user_id=current_user.id,
        reason=payload.reason,
        created_at=datetime.now(timezone.utc),
    )
    db.add(review)
    db.commit()
    return {"id": review.id, "status": review.status}
