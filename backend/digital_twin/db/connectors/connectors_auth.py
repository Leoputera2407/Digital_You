from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from digital_twin.db.model import CSRFToken
from digital_twin.utils.logging import async_log_sqlalchemy_error, setup_logger

logger = setup_logger()


@async_log_sqlalchemy_error(logger)
async def async_store_csrf(credential_id: int, csrf: str, db_session: AsyncSession) -> Optional[CSRFToken]:
    stmt = select(CSRFToken).where(CSRFToken.credential_id == credential_id)
    result = await db_session.execute(stmt)
    token = result.scalars().first()

    if token:
        # If existing token found, update it
        token.csrf_token = csrf
    else:
        # If no token found, create new
        token = CSRFToken(credential_id=credential_id, csrf_token=csrf)
        db_session.add(token)

    await db_session.commit()
    return token


@async_log_sqlalchemy_error(logger)
async def async_consume_csrf(credential_id: int, db_session: AsyncSession) -> Optional[CSRFToken]:
    stmt = (
        select(CSRFToken)
        .where(CSRFToken.credential_id == credential_id)
        .order_by(CSRFToken.created_at.desc())
    )
    result = await db_session.execute(stmt)
    token = result.scalars().first()

    if token:
        # If token found, delete it and return
        csrf_token = token.csrf_token
        delete_stmt = delete(CSRFToken).where(
            CSRFToken.credential_id == credential_id, CSRFToken.csrf_token == csrf_token
        )
        result = await db_session.execute(delete_stmt)
        await db_session.commit()
        return token

    else:
        return None
