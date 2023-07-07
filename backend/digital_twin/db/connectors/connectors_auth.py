from sqlalchemy.orm import Session
from sqlalchemy import delete, select
from datetime import datetime
from typing import Optional
from digital_twin.utils.logging import setup_logger, log_sqlalchemy_error
from digital_twin.db.model import CSRFToken

logger = setup_logger()

@log_sqlalchemy_error(logger)
def store_csrf(credential_id: int, csrf: str, db_session: Session) -> Optional[CSRFToken]:
    stmt = select(CSRFToken).where(CSRFToken.credential_id == credential_id)
    result = db_session.execute(stmt)
    token = result.scalars().first()

    if token:
        # If existing token found, update it
        token.csrf_token = csrf
    else:
        # If no token found, create new
        token = CSRFToken(credential_id=credential_id, csrf_token=csrf)
        db_session.add(token)

    db_session.commit()
    return token


@log_sqlalchemy_error(logger)
def consume_csrf(credential_id: int, db_session: Session) -> Optional[CSRFToken]:
    stmt = (
        select(CSRFToken)
        .where(CSRFToken.credential_id == credential_id)
        .order_by(CSRFToken.created_at.desc()) 
    )
    result = db_session.execute(stmt)
    token = result.scalars().first()

    if token:
        # If token found, delete it and return
        csrf_token = token.csrf_token
        delete_stmt = delete(CSRFToken).where(
            CSRFToken.credential_id == credential_id,
            CSRFToken.csrf_token == csrf_token
        )
        result = db_session.execute(delete_stmt)
        if result.rowcount == 0:
            raise Exception('Failed to consume CSRF token')
        db_session.commit()
        return token

    else:
        return None