"""Owner-scoped loading and text extraction for chat attachments."""

from __future__ import annotations

import base64
import io
from dataclasses import dataclass
from zipfile import BadZipFile, ZipFile
from xml.etree import ElementTree

from fastapi import HTTPException, status
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import MediaContentDB, MediaDB
from app.services.ai import transcribe_audio

MAX_EXTRACTED_TEXT_CHARS = 40_000
MAX_PDF_PAGES = 100


@dataclass(frozen=True)
class ChatAttachment:
    filename: str
    content_type: str
    text: str | None = None
    image_data_url: str | None = None
    file_data_url: str | None = None


def _extract_pdf_text(content: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(content), strict=False)
        text = "\n".join(
            page.extract_text() or "" for page in reader.pages[:MAX_PDF_PAGES]
        )
    except (PdfReadError, OSError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The uploaded PDF could not be read.",
        ) from error
    return text


def _extract_docx_text(content: bytes) -> str:
    try:
        with ZipFile(io.BytesIO(content)) as archive:
            document = ElementTree.fromstring(archive.read("word/document.xml"))
    except (BadZipFile, KeyError, ElementTree.ParseError) as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The uploaded Word document could not be read.",
        ) from error
    namespace = {"word": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    return "\n".join(
        "".join(node.text or "" for node in paragraph.findall(".//word:t", namespace))
        for paragraph in document.findall(".//word:p", namespace)
    )


def load_chat_attachments(
    media_ids: list[str],
    user_id: int,
    db: Session,
) -> list[ChatAttachment]:
    if len(set(media_ids)) != len(media_ids):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Each attachment may only be included once.",
        )
    if not media_ids:
        return []

    rows = db.execute(
        select(MediaDB, MediaContentDB)
        .join(MediaContentDB, MediaContentDB.media_id == MediaDB.id)
        .where(
            MediaDB.id.in_(media_ids),
            MediaDB.user_id == user_id,
            MediaDB.active.is_(True),
        )
    ).all()
    if len(rows) != len(media_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more attachments were not found.",
        )
    attachments_by_id = {media.id: (media, stored.content) for media, stored in rows}

    attachments: list[ChatAttachment] = []
    for media_id in media_ids:
        media, content = attachments_by_id[media_id]
        if media.kind == "image":
            encoded = base64.b64encode(content).decode("ascii")
            attachments.append(
                ChatAttachment(
                    filename=media.filename,
                    content_type=media.content_type,
                    image_data_url=f"data:{media.content_type};base64,{encoded}",
                )
            )
        elif media.kind == "document":
            file_data_url = None
            if media.content_type == "application/pdf":
                extracted_text = _extract_pdf_text(content)
                file_data_url = (
                    f"data:application/pdf;base64,"
                    f"{base64.b64encode(content).decode('ascii')}"
                )
            elif media.content_type == (
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ):
                extracted_text = _extract_docx_text(content)
            else:
                try:
                    extracted_text = content.decode("utf-8-sig")
                except UnicodeDecodeError as error:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"{media.filename} must contain UTF-8 text.",
                    ) from error
            truncated = len(extracted_text) > MAX_EXTRACTED_TEXT_CHARS
            extracted_text = extracted_text[:MAX_EXTRACTED_TEXT_CHARS].strip()
            if not extracted_text and not file_data_url:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"No readable text was found in {media.filename}.",
                )
            attachments.append(
                ChatAttachment(
                    filename=media.filename,
                    content_type=media.content_type,
                    text=(
                        f"{extracted_text}\n[Text extraction truncated for analysis.]"
                        if truncated
                        else extracted_text or None
                    ),
                    file_data_url=file_data_url,
                )
            )
        elif media.kind == "audio":
            transcript = transcribe_audio(
                media.filename,
                media.content_type,
                content,
            )
            attachments.append(
                ChatAttachment(
                    filename=media.filename,
                    content_type=media.content_type,
                    text=transcript,
                )
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="This attachment type is not supported for chat analysis.",
            )
    return attachments
