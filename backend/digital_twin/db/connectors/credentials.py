from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import or_, and_

from digital_twin.db.engine import get_sqlalchemy_engine
from digital_twin.db.model import Credential, User
from digital_twin.server.model import CredentialBase, ObjectCreationIdResponse

from digital_twin.utils.logging import (
    setup_logger, 
    log_sqlalchemy_error,
    async_log_sqlalchemy_error,
)

logger = setup_logger()


def mask_string(
        sensitive_str: str
) -> str:
    return sensitive_str[0:4] + "****" + sensitive_str[-4:] 


def mask_credential_dict(
        credential_dict: dict[str, Any]
) -> dict[str, str]:
    masked_creds = {}
    for key, val in credential_dict.items():
        if not isinstance(val, str):
            raise ValueError(
                "Unable to mask credentials of type other than string, cannot process request."
            )

        masked_creds[key] = mask_string(val)
    return masked_creds

@log_sqlalchemy_error(logger)
def fetch_credentials(
    user: User | None,
    organization_id: int,
    db_session: Session,
) -> list[Credential]:
    stmt = select(Credential)
    if user:
        stmt = stmt.where(
            and_(
                or_(
                    Credential.user_id == user.id, 
                    Credential.user_id.is_(None)
                ),
                Credential.organization_id == organization_id
            )
        )
    results = db_session.scalars(stmt).unique()
    return list(results.all())

@log_sqlalchemy_error(logger)
def fetch_credential_by_id_and_org(
    credential_id: int,
    user: User | None, 
    organization_id: UUID | None, 
    db_session: Session
) -> Credential | None:
    stmt = select(Credential).where(
            Credential.id == credential_id, 
        )
    if user:
        stmt = stmt.where(
            or_(
                Credential.user_id == user.id, 
                Credential.user_id.is_(None)
            )
        )
    if organization_id:
        stmt = stmt.where(
            or_(
                Credential.organization_id == organization_id,
                Credential.organization_id.is_(None)
            )
        )
    result = db_session.execute(stmt)
    credential = result.scalars().first()
    return credential

@async_log_sqlalchemy_error
async def async_fetch_credential_by_id_and_org(
    credential_id: int,
    user: User | None, 
    organization_id: UUID | None, 
    db_session: AsyncSession
) -> Credential | None:
    try:
        stmt = select(Credential).where(
                Credential.id == credential_id, 
            )
        if user:
            stmt = stmt.where(
                or_(
                    Credential.user_id == user.id, 
                    Credential.user_id.is_(None)
                )
            )
        if organization_id:
            stmt = stmt.where(
                or_(
                    Credential.organization_id == organization_id,
                    Credential.organization_id.is_(None)
                )
            )
        result = await db_session.execute(stmt)
        credential = result.scalars().first()
        return credential

    except Exception as e:
        logger.error(f"Error executing SQL query: {e}")
        return None


@log_sqlalchemy_error(logger)
def create_credential(
    credential_data: CredentialBase,
    user: User,
    organization_id: int,
    db_session: Session,
) -> ObjectCreationIdResponse:
    credential = Credential(
        credential_json=credential_data.credential_json,
        user_id=user.id if user else None,
        public_doc=credential_data.public_doc,
        organization_id=organization_id,
    )
    db_session.add(credential)
    db_session.commit()

    return ObjectCreationIdResponse(id=credential.id)

@log_sqlalchemy_error(logger)
async def async_create_credential(
    credential_data: CredentialBase,
    user: User,
    organization_id: int,
    db_session: AsyncSession,
) -> ObjectCreationIdResponse:
    credential = Credential(
        credential_json=credential_data.credential_json,
        user_id=user.id if user else None,
        public_doc=credential_data.public_doc,
        organization_id=organization_id,
    )
    db_session.add(credential)
    await db_session.commit()

    return ObjectCreationIdResponse(id=credential.id)

@log_sqlalchemy_error(logger)
def update_credential(
    credential_id: int,
    credential_data: CredentialBase,
    user: User,
    organization_id: int,
    db_session: Session,
) -> Credential | None:
    credential = fetch_credential_by_id_and_org(
        credential_id, 
        user, 
        organization_id,
        db_session
    )
    if credential is None:
        return None

    credential.credential_json = credential_data.credential_json
    credential.user_id = user.id if user is not None else None
    credential.public_doc = credential_data.public_doc
    credential.organization_id = organization_id

    db_session.commit()
    return credential

@log_sqlalchemy_error(logger)
def update_credential_json(
    credential_id: int,
    credential_json: dict[str, Any],
    organization_id: int,
    user: User,
    db_session: Session,
) -> Credential | None:
    credential = fetch_credential_by_id_and_org(
        credential_id, 
        user, 
        organization_id,
        db_session
    )
    if credential is None:
        return None
    credential.credential_json = credential_json

    db_session.commit()
    return credential

def backend_update_credential_json(
    credential: Credential,
    credential_json: dict[str, Any],
    db_session: Session,
) -> None:
    """This should be used only in backend"""
    credential.credential_json = credential_json
    db_session.commit()


@log_sqlalchemy_error(logger)
def delete_credential(
    credential_id: int,
    user: User,
    organization_id: int,
    db_session: Session,
) -> None:
    credential = fetch_credential_by_id_and_org(
        credential_id,
        user, 
        organization_id,
        db_session
    )
    if credential is None:
        raise ValueError(
            f"Credential by provided id {credential_id} does not exist or does not belong to user or organization"
        )

    db_session.delete(credential)
    db_session.commit()

# TODO: This maybe ok to be removed
@log_sqlalchemy_error(logger)
def create_initial_public_credential() -> None:
    public_cred_id = 0
    error_msg = (
        "DB is not in a valid initial state."
        "There must exist an empty public credential for data connectors that do not require additional Auth."
    )
    with Session(get_sqlalchemy_engine(), expire_on_commit=False) as db_session:
        first_credential = fetch_credential_by_id_and_org(
            public_cred_id, 
            None, 
            None,
            db_session
        )

        if first_credential is not None:
            if (
                first_credential.credential_json != {}
                or first_credential.public_doc is False
            ):
                raise ValueError(error_msg)
            return

        credential = Credential(
            id=public_cred_id, credential_json={}, user_id=None, public_doc=True
        )
        db_session.add(credential)
        db_session.commit()
