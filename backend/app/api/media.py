"""Bounded media upload metadata routes."""

import mimetypes
from io import BytesIO
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated
from zipfile import BadZipFile, ZipFile

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.auth.security import get_current_user
from app.core.config import (
    ALLOWED_AUDIO_TYPES,
    ALLOWED_DOCUMENT_TYPES,
    ALLOWED_IMAGE_TYPES,
    MAX_MEDIA_BYTES,
)
from app.db.database import MediaContentDB, MediaDB, UserDB, get_db

router = APIRouter(prefix="/media", tags=["media"])

DOCX_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
MAX_ACTIVE_MEDIA_BYTES = 64 * 1024 * 1024
MAX_ACTIVE_MEDIA_FILES = 20
MEDIA_RETENTION = timedelta(hours=24)


def _validate_content(content: bytes, content_type: str) -> None:
    valid = True
    if content_type == "image/jpeg":
        valid = content.startswith(b"\xff\xd8\xff")
    elif content_type == "image/png":
        valid = content.startswith(b"\x89PNG\r\n\x1a\n")
    elif content_type == "image/webp":
        valid = content.startswith(b"RIFF") and content[8:12] == b"WEBP"
    elif content_type == "application/pdf":
        valid = content.startswith(b"%PDF-")
    elif content_type in {"audio/wav", "audio/x-wav", "audio/wave"}:
        valid = (
            content.startswith(b"RIFF") and content[8:12] == b"WAVE"
        ) or (content.startswith(b"RF64") and content[8:12] == b"WAVE")
    elif content_type == "audio/webm":
        valid = content.startswith(b"\x1aE\xdf\xa3")
    elif content_type == "audio/mp4":
        valid = len(content) >= 8 and content[4:8] == b"ftyp"
    elif content_type == "audio/mpeg":
        valid = content.startswith(b"ID3") or (
            len(content) >= 2 and content[0] == 0xFF and content[1] & 0xE0 == 0xE0
        )
    elif content_type == DOCX_TYPE:
        try:
            with ZipFile(BytesIO(content)) as archive:
                valid = "word/document.xml" in archive.namelist()
        except BadZipFile:
            valid = False
    elif content_type in ALLOWED_DOCUMENT_TYPES:
        try:
            content.decode("utf-8-sig")
            valid = b"\x00" not in content
        except UnicodeDecodeError:
            valid = False
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="File content does not match its declared type.",
        )


def _expire_pending_uploads(user_id: int, db: Session, now: datetime) -> None:
    expired = db.scalars(
        select(MediaDB).where(
            MediaDB.user_id == user_id,
            MediaDB.active.is_(True),
            MediaDB.created_at < now - MEDIA_RETENTION,
        )
    ).all()
    if not expired:
        return
    expired_ids = [media.id for media in expired]
    for media in expired:
        media.active = False
    db.execute(
        delete(MediaContentDB).where(MediaContentDB.media_id.in_(expired_ids))
    )
    db.flush()


@router.post("")
async def upload_media(
    file: Annotated[UploadFile, File(...)],
    kind: str,
    current_user: Annotated[UserDB, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    content_type = (file.content_type or "").split(";", maxsplit=1)[0].lower()
    if content_type in {"", "application/octet-stream"}:
        content_type = mimetypes.guess_type(file.filename or "")[0] or content_type
    allowed_types = {
        "image": ALLOWED_IMAGE_TYPES,
        "audio": ALLOWED_AUDIO_TYPES,
        "document": ALLOWED_DOCUMENT_TYPES,
    }.get(kind, set())
    if content_type not in allowed_types:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Unsupported media type")
    content = await file.read(MAX_MEDIA_BYTES + 1)
    if len(content) > MAX_MEDIA_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Media exceeds 8 MiB limit")
    if not content:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Uploaded file is empty.")
    _validate_content(content, content_type)
    filename = (file.filename or "upload").replace("\\", "/").rsplit("/", maxsplit=1)[-1]
    now = datetime.now(timezone.utc)
    _expire_pending_uploads(current_user.id, db, now)
    active_bytes = db.scalar(
        select(func.coalesce(func.sum(MediaDB.size_bytes), 0)).where(
            MediaDB.user_id == current_user.id,
            MediaDB.active.is_(True),
        )
    )
    active_count = db.scalar(
        select(func.count()).select_from(MediaDB).where(
            MediaDB.user_id == current_user.id,
            MediaDB.active.is_(True),
        )
    )
    if active_bytes + len(content) > MAX_ACTIVE_MEDIA_BYTES or active_count >= MAX_ACTIVE_MEDIA_FILES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Pending uploads exceed the per-account storage limit.",
        )
    media = MediaDB(
        id=f"media_{uuid.uuid4().hex}",
        user_id=current_user.id,
        kind=kind,
        filename=filename[:255],
        content_type=content_type,
        size_bytes=len(content),
        created_at=now,
    )
    db.add_all(
        [
            media,
            MediaContentDB(media_id=media.id, content=content),
        ]
    )
    db.commit()
    return {
        "id": media.id,
        "kind": media.kind,
        "filename": media.filename,
        "content_type": media.content_type,
        "size_bytes": media.size_bytes,
    }


@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def discard_media(
    media_id: str,
    current_user: Annotated[UserDB, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    media = db.scalar(
        select(MediaDB).where(
            MediaDB.id == media_id,
            MediaDB.user_id == current_user.id,
        )
    )
    if media is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found.")
    media.active = False
    db.execute(
        delete(MediaContentDB).where(MediaContentDB.media_id == media.id)
    )
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
