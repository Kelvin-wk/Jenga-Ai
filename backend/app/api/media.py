"""Bounded media upload metadata routes."""

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.auth.security import get_current_user
from app.core.config import ALLOWED_AUDIO_TYPES, ALLOWED_IMAGE_TYPES, MAX_MEDIA_BYTES
from app.db.database import MediaDB, UserDB, get_db

router = APIRouter(prefix="/media", tags=["media"])


@router.post("")
async def upload_media(
    file: Annotated[UploadFile, File(...)],
    kind: str,
    current_user: Annotated[UserDB, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    allowed_types = ALLOWED_IMAGE_TYPES if kind == "image" else ALLOWED_AUDIO_TYPES if kind == "audio" else set()
    if not allowed_types or file.content_type not in allowed_types:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Unsupported media type")
    content = await file.read(MAX_MEDIA_BYTES + 1)
    if len(content) > MAX_MEDIA_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Media exceeds 8 MiB limit")
    media = MediaDB(
        id=f"media_{uuid.uuid4().hex}",
        user_id=current_user.id,
        kind=kind,
        filename=file.filename or "upload",
        content_type=file.content_type,
        size_bytes=len(content),
        created_at=datetime.now(timezone.utc),
    )
    db.add(media)
    db.commit()
    return {"id": media.id, "kind": media.kind, "content_type": media.content_type, "size_bytes": media.size_bytes}
