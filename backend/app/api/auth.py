"""Authentication routes."""

from typing import Annotated
from fastapi import Request
from sqlalchemy import select

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.auth.security import authenticate_user, create_access_token
from app.core.config import SESSION_COOKIE_NAME
from app.core.sessions import create_session
from app.db.database import SessionDB, get_db, hash_session_token, utc_now
from app.schemas.auth import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(
    credentials: LoginRequest,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    user = authenticate_user(db, credentials.username, credentials.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    session_token = create_session(db, user)
    response.set_cookie(SESSION_COOKIE_NAME, session_token, httponly=True, samesite="lax", secure=False, max_age=8 * 3600)
    return TokenResponse(
        access_token=create_access_token(user.username, user.role),
        token_type="bearer",
        role=user.role,  # type: ignore[arg-type]
    )


@router.get("/me")
def me(request: Request, db: Annotated[Session, Depends(get_db)]) -> dict[str, object]:
    from app.core.sessions import require_session

    _, user = require_session(request, db)
    return {"id": user.id, "username": user.username, "role": user.role}


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, db: Annotated[Session, Depends(get_db)]) -> None:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        session = db.scalar(select(SessionDB).where(SessionDB.token_hash == hash_session_token(token)))
        if session is not None:
            session.revoked_at = utc_now()
            db.commit()
    response.delete_cookie(SESSION_COOKIE_NAME)
