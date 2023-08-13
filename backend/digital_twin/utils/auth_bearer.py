import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from jose.exceptions import JWTError

from digital_twin.config.app_config import DISABLE_AUTHENTICATION, JWT_ALGORITHM, JWT_SECRET_KEY
from digital_twin.db.model import User


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str):
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            options={"verify_aud": False},
        )
        return payload
    except JWTError as e:
        return None


def verify_token(token: str):
    payload = decode_access_token(token)
    return payload is not None


def get_user_email_from_token(token: str):
    payload = decode_access_token(token)
    if payload:
        return payload.get("email")
    return "none"


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: Optional[HTTPAuthorizationCredentials] = await super().__call__(request)
        if self.check_scheme(credentials) and credentials:
            token = credentials.credentials
            return await self.authenticate(token)
        else:
            return HTTPException(status_code=403, detail="Invalid authorization code.")

    def check_scheme(self, credentials) -> bool:
        if credentials and not credentials.scheme == "Bearer":
            raise HTTPException(status_code=402, detail="Invalid authorization scheme.")
        elif not credentials:
            raise HTTPException(status_code=403, detail="Invalid authorization code.")

        return True

    async def authenticate(self, token: str):
        # TODO: Enable non-authenticated endpoints, for easier dev testing
        if DISABLE_AUTHENTICATION:
            return self.get_test_user()
        elif verify_token(token):
            return decode_access_token(token)
        else:
            raise HTTPException(status_code=402, detail="Invalid token or expired token.")

    def get_test_user(self):
        return {"email": "test@example.com"}  # replace with test user information


# TODO: Refactor to use this getUser instead of having to pass supabase_user_id all the time
def get_current_user(credentials: dict = Depends(JWTBearer())) -> User:
    return User(
        id=credentials.get("id"),
        first_name=credentials.get("first_name"),
        last_name=credentials.get("last_name"),
        email=credentials.get("email"),
        qdrant_collection_key=credentials.get("qdrant_collection_key"),
    )
