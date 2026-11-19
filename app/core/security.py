from datetime import datetime, timedelta, UTC
from pwdlib import PasswordHash
import jwt
from app.core.config import settings
from fastapi import Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordBearer
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated
from app.models.user import User
from sqlalchemy import select
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

import hashlib
import secrets


password_hash = PasswordHash.recommended()
http_bearer = HTTPBearer()
# oauth2_sheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token")


def hash_password(password: str) -> str :
    return password_hash.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)
def generate_activated_code() -> str:
    return str(secrets.randbelow(900_000) + 100_000)
def hash_activated_code(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()

def verify_activated_code(otp,otp_hash) ->bool:
    return  hash_activated_code(otp)==otp_hash
def generate_refresh_token() ->str:
    return secrets.token_urlsafe(32)
def hash_refresh_token(token:str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
def create_access_token(data: dict, expires_delta: int | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + timedelta(minutes=expires_delta)
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.access_token_expires_minute
        )

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key.get_secret_value(),
        algorithm=settings.algorithm
    )

    return encoded_jwt
def verify_access_token(token: str):
    try:
        payload = jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            algorithms=[settings.algorithm],
            options={"require": ["exp", "sub"]},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    else:
        return payload.get("sub")


async def get_current_user(
    ccredentials: Annotated[
        HTTPAuthorizationCredentials,
        Depends(http_bearer)
    ],
    # token: Annotated[str, Depends(oauth2_sheme)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    token = ccredentials.credentials
    user_id = verify_access_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
         user_id = UUID(user_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    result = await db.execute(
        select(User).where(User.id == user_id)
    )

    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Check account status
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is not active"
        )

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]




def require_role(*allowed_roles: str):

    def checker(current_user: CurrentUser) -> User:

        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to do this"
            )

        return current_user

    return checker