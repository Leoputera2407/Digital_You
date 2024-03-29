import contextlib
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from jose.exceptions import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from digital_twin.config.app_config import DISABLE_AUTHENTICATION, JWT_ALGORITHM, JWT_SECRET_KEY
from digital_twin.db.engine import get_async_session_generator
from digital_twin.db.model import Organization, User, UserRole
from digital_twin.db.user import async_get_user_by_email, async_get_user_org_by_user_and_org_id
from digital_twin.utils.logging import setup_logger

logger = setup_logger()


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


class AuthBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        try:
            credentials: Optional[HTTPAuthorizationCredentials] = await super().__call__(request)
        except Exception as e:
            logger.exception("Exception raised while extracting the auth bearer: %s", e)
            raise HTTPException(status_code=403, detail="No auth bearer provided.")

        if self.check_scheme(credentials) and credentials:
            token = credentials.credentials
            return await self.authenticate(token)
        else:
            return HTTPException(status_code=403, detail="Invalid authorization code.")

    def check_scheme(self, credentials: Optional[HTTPAuthorizationCredentials]) -> bool:
        if credentials and not credentials.scheme == "Bearer":
            logger.info("Invalid authorization scheme.")
            raise HTTPException(status_code=402, detail="Invalid authorization scheme.")
        elif not credentials:
            logger.info("No credentials provided.")
            raise HTTPException(status_code=403, detail="Invalid authorization code.")
        return True

    async def authenticate(self, token: str):
        if DISABLE_AUTHENTICATION:
            return self.get_test_user()
        elif verify_token(token):
            return decode_access_token(token)
        else:
            logger.info("Invalid token or expired token.")
            raise HTTPException(status_code=402, detail="Invalid token or expired token.")

    def get_test_user(self):
        # Replace by test user details if needed
        return {"email": "test@example.com"}


async def create_get_fake_user() -> User:
    get_async_session_context = contextlib.asynccontextmanager(get_async_session_generator)  # type:ignore

    logger.info("Creating fake user due to Auth being turned off")
    async with get_async_session_context() as session:
        # create fake organization
        fake_org = Organization(
            name="Fake Organization",
        )
        session.add(fake_org)
        # flush the session to get the ID of fake_org
        await session.flush()

        # create fake user
        fake_user = User(
            email="test@example.com",
            organization_id=fake_org.id,
            first_name="Test",
            last_name="User",
        )
        session.add(fake_user)
        await session.commit()
        return fake_user


async def current_user(
    db_session: AsyncSession = Depends(get_async_session_generator),
    decoded_token: dict = Depends(AuthBearer()),
) -> User:
    email = decoded_token.get("email")
    if email is None:
        logger.info("Cannot find email in decoded auth token.")
        raise HTTPException(status_code=400, detail="Invalid authorization code.")

    user = await async_get_user_by_email(db_session, email)
    if user is None:
        logger.info("Cannot find user with email: %s", email)
        raise HTTPException(status_code=400, detail="User not found.")
    return user


async def current_admin_for_org(
    organization_id: UUID,  # NOTE: This is a path parameter, and it's
    # important that the server also named the variable "organization_id"
    user: User = Depends(current_user),
    db_session: AsyncSession = Depends(get_async_session_generator),
) -> User:
    association = await async_get_user_org_by_user_and_org_id(db_session, user.id, organization_id)
    if not association or association.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Access denied. User is not an admin for this organization.",
        )

    return user
