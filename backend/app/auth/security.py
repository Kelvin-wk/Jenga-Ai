"""JWT creation and database-backed user authentication."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import UserDB, get_db, pwd_context

SECRET_KEY = os.getenv("JENGA_SECRET_KEY", "change-this-development-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def create_access_token(username: str, role: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": username, "role": role, "exp": expires}, SECRET_KEY, algorithm=ALGORITHM)


def authenticate_user(db: Session, username: str, password: str) -> UserDB | None:
    user = db.scalar(select(UserDB).where(UserDB.username == username))
    if user is None or not pwd_context.verify(password, user.hashed_password):
        return None
    return user


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> UserDB:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role")
        if not isinstance(username, str) or role not in {"engineer", "customer"}:
            raise credentials_error
    except (JWTError, TypeError):
        raise credentials_error from None

    user = db.scalar(select(UserDB).where(UserDB.username == username))
    # The role is checked against the database as well as the token. This
    # prevents stale or client-forged role claims from granting access.
    if user is None or user.role != role:
        raise credentials_error
    return user
