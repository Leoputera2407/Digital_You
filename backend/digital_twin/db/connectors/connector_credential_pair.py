from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, aliased, joinedload
from sqlalchemy.sql.expression import and_
from sqlalchemy.ext.asyncio import AsyncSession

from digital_twin.db.connectors.connectors import (
    async_fetch_connector_by_id_and_org,
) 
from digital_twin.db.connectors.credentials import (
    async_fetch_credential_by_id_and_org,
)
from digital_twin.db.model import (
    ConnectorCredentialPair,
    IndexingStatus,
    User,
    Credential,
    Connector,
)
from digital_twin.server.model import StatusResponse
from digital_twin.utils.logging import (
    setup_logger, 
    log_sqlalchemy_error,
    async_log_sqlalchemy_error,
)

logger = setup_logger()

@async_log_sqlalchemy_error(logger)
async def async_fetch_connector_by_org_id(
    db_session: AsyncSession, 
    organization_id: UUID,
    include_disabled: bool = True,
) -> list[ConnectorCredentialPair]:
    ConnectorAlias = aliased(Connector)
    CredentialAlias = aliased(Credential)

    stmt = select(ConnectorCredentialPair).join(
        ConnectorAlias, ConnectorCredentialPair.connector_id == ConnectorAlias.id
    ).join(
        CredentialAlias, ConnectorCredentialPair.credential_id == CredentialAlias.id
    ).where(
        and_(
            ConnectorAlias.organization_id == organization_id,
            CredentialAlias.organization_id == organization_id,
        )
    )
    
    if not include_disabled:
        stmt = stmt.where(
            ConnectorAlias.disabled == False
        )
    results = db_session.scalars(stmt)
    return list(results.unique().all())


@log_sqlalchemy_error(logger)
def get_connector_credential_pair(
    connector_id: int,
    credential_id: int,
    organization_id: UUID | None,
    db_session: Session,
) -> ConnectorCredentialPair | None:
    ConnectorAlias = aliased(Connector)
    CredentialAlias = aliased(Credential)
    stmt = select(ConnectorCredentialPair).join(
        ConnectorAlias, ConnectorCredentialPair.connector_id == ConnectorAlias.id
    ).join(
        CredentialAlias, ConnectorCredentialPair.credential_id == CredentialAlias.id
    ).where(
        and_(
            ConnectorCredentialPair.connector_id == connector_id,
            ConnectorCredentialPair.credential_id == credential_id,
        )
    )
    if organization_id is not None:
        stmt = stmt.where(
            and_(
                ConnectorAlias.organization_id == organization_id,
                CredentialAlias.organization_id == organization_id,
            )
        )
    
    result = db_session.execute(stmt)
    return result.unique().scalar_one_or_none()

@async_log_sqlalchemy_error(logger)
async def async_get_connector_credential_pair(
    connector_id: int,
    credential_id: int,
    organization_id: UUID | None,
    db_session: AsyncSession,
) -> ConnectorCredentialPair | None:
    ConnectorAlias = aliased(Connector)
    CredentialAlias = aliased(Credential)
    stmt = select(ConnectorCredentialPair).join(
        ConnectorAlias, ConnectorCredentialPair.connector_id == ConnectorAlias.id
    ).join(
        CredentialAlias, ConnectorCredentialPair.credential_id == CredentialAlias.id
    ).where(
        and_(
            ConnectorCredentialPair.connector_id == connector_id,
            ConnectorCredentialPair.credential_id == credential_id,
        )
    )
    if organization_id is not None:
        stmt = stmt.where(
            and_(
                ConnectorAlias.organization_id == organization_id,
                CredentialAlias.organization_id == organization_id,
            )
        )
    
    result = await db_session.execute(stmt)
    return result.unique().scalar_one_or_none()


@async_log_sqlalchemy_error(logger)
async def async_get_connector_credential_pairs(
    db_session: AsyncSession, 
    organization_id: UUID,
    include_disabled: bool = True,
) -> list[ConnectorCredentialPair]:
    stmt = select(ConnectorCredentialPair).options(
        joinedload(ConnectorCredentialPair.connector).load_only(
            Connector.id, 
            Connector.organization_id, 
            Connector.disabled, 
            Connector.name, 
            Connector.source, 
            Connector.input_type, 
            Connector.connector_specific_config, 
            Connector.refresh_freq, 
            Connector.created_at, 
            Connector.updated_at,
        ),
        joinedload(ConnectorCredentialPair.connector).subqueryload(Connector.credentials),
        joinedload(ConnectorCredentialPair.credential).load_only(
            Credential.id, 
            Credential.organization_id, 
            Credential.credential_json, 
            Credential.user_id, 
            Credential.public_doc, 
            Credential.created_at, 
            Credential.updated_at,
        ),
        joinedload(ConnectorCredentialPair.credential).subqueryload(Credential.user)
    ).where(
        and_(
            ConnectorCredentialPair.connector.has(Connector.organization_id == organization_id),
            ConnectorCredentialPair.credential.has(Credential.organization_id == organization_id)
        )
    )
    
    if not include_disabled:
        stmt = stmt.where(
            ConnectorCredentialPair.connector.has(Connector.disabled == False)
        )
    results = await db_session.scalars(stmt)
    return list(results.unique().all())


@log_sqlalchemy_error(logger)
def backend_update_connector_credential_pair(
    connector_id: int,
    credential_id: int,
    attempt_status: IndexingStatus,
    net_docs: int | None,
    db_session: Session,
) -> bool:
    """
    This is mostly used in the backend, and will
    pull update regardless of the organization_id
    """
    try:
        cc_pair = get_connector_credential_pair(
            connector_id, 
            credential_id,
            organization_id = None, 
            db_session = db_session,
        )
        if not cc_pair:
            logger.warning(
                f"Attempted to update pair for connector id {connector_id} "
                f"and credential id {credential_id}"
            )
            return False
        cc_pair.last_attempt_status = attempt_status
        if attempt_status == IndexingStatus.SUCCESS:
            cc_pair.last_successful_index_time = func.now()  # type:ignore
        if net_docs is not None:
            cc_pair.total_docs_indexed += net_docs
        db_session.commit()
        return True
    except Exception as e:
        logger.error(f"Failed to update connector credential pair: {e}")
        return False

@async_log_sqlalchemy_error(logger)
async def async_update_connector_credential_pair(
    connector_id: int,
    credential_id: int,
    organization_id: UUID,
    attempt_status: IndexingStatus,
    net_docs: int | None,
    db_session: AsyncSession,
) -> bool:
    try:
        cc_pair = await async_get_connector_credential_pair(
            connector_id, 
            credential_id,
            organization_id, 
            db_session
        )
        if not cc_pair:
            logger.warning(
                f"Attempted to update pair for connector id {connector_id} "
                f"and credential id {credential_id}"
            )
            return False
        cc_pair.last_attempt_status = attempt_status
        if attempt_status == IndexingStatus.SUCCESS:
            cc_pair.last_successful_index_time = func.now()  # type:ignore
        if net_docs is not None:
            cc_pair.total_docs_indexed += net_docs
        await db_session.commit()
        return True
    except Exception as e:
        logger.error(f"Failed to update connector credential pair: {e}")
        return False

@async_log_sqlalchemy_error(logger)
async def async_remove_credential_from_connector(
    connector_id: int,
    credential_id: int,
    organization_id: UUID,
    user: User,
    db_session: AsyncSession,
) -> StatusResponse[int]:
    connector = await async_fetch_connector_by_id_and_org(
        connector_id, 
        organization_id,
        db_session,
    )
    credential = await async_fetch_credential_by_id_and_org(
        credential_id, 
        user, 
        organization_id,
        db_session,
    )

    if connector is None:
        raise HTTPException(status_code=404, detail="Connector does not exist")

    if credential is None:
        raise HTTPException(
            status_code=404,
            detail="Credential does not exist or does not belong to user",
        )

    association = (
        await db_session.execute(
            select(ConnectorCredentialPair)
            .where(
                ConnectorCredentialPair.connector_id == connector_id,
                ConnectorCredentialPair.credential_id == credential_id,
            )
        )
    ).scalars().first()

    if association is not None:
        await db_session.delete(association)
        await db_session.commit()
        return StatusResponse(
            success=True,
            message=f"Credential {credential_id} removed from Connector",
            data=connector_id,
        )

    return StatusResponse(
        success=False,
        message=f"Connector already does not have Credential {credential_id}",
        data=connector_id,
    )

@async_log_sqlalchemy_error(logger)
async def async_add_credential_to_connector(
    connector_id: int,
    credential_id: int,
    organization_id: UUID,
    user: User,
    db_session: AsyncSession,
) -> StatusResponse[int]:
    connector = await async_fetch_connector_by_id_and_org(
        connector_id, 
        organization_id,
        db_session,
    )
    credential = await async_fetch_credential_by_id_and_org(
        credential_id, 
        user, 
        organization_id,
        db_session
    )

    if connector is None:
        raise HTTPException(status_code=404, detail="Connector does not exist")

    if credential is None:
        raise HTTPException(
            status_code=401,
            detail="Credential does not exist or does not belong to user",
        )

    existing_association = (
        await db_session.execute(
            select(ConnectorCredentialPair)
            .where(
                ConnectorCredentialPair.connector_id == connector_id,
                ConnectorCredentialPair.credential_id == credential_id,
            )
        )
    ).scalars().first()

    if existing_association is not None:
        return StatusResponse(
            success=False,
            message=f"Connector already has Credential {credential_id}",
            data=connector_id,
        )

    association = ConnectorCredentialPair(
        connector_id=connector_id,
        credential_id=credential_id,
        last_attempt_status=IndexingStatus.NOT_STARTED,
    )
    db_session.add(association)
    await db_session.commit()

    return StatusResponse(
        success=True,
        message=f"New Credential {credential_id} added to Connector",
        data=connector_id,
    )

@async_log_sqlalchemy_error(logger)
async def async_remove_credential_from_connector(
    connector_id: int,
    credential_id: int,
    organization_id: UUID,
    user: User,
    db_session: AsyncSession,
) -> StatusResponse[int]:
    connector = await async_fetch_connector_by_id_and_org(
        connector_id, 
        organization_id,
        db_session,
    )
    credential = await async_fetch_credential_by_id_and_org(
        credential_id, 
        user, 
        organization_id,
        db_session,
    )

    if connector is None:
        raise HTTPException(status_code=404, detail="Connector does not exist")

    if credential is None:
        raise HTTPException(
            status_code=404,
            detail="Credential does not exist or does not belong to user",
        )

    association = (
        await db_session.execute(
            select(ConnectorCredentialPair)
            .where(
                ConnectorCredentialPair.connector_id == connector_id,
                ConnectorCredentialPair.credential_id == credential_id,
            )
        )
    ).scalars().first()

    if association is not None:
        await db_session.delete(association)
        await db_session.commit()
        return StatusResponse(
            success=True,
            message=f"Credential {credential_id} removed from Connector",
            data=connector_id,
        )

    return StatusResponse(
        success=False,
        message=f"Connector already does not have Credential {credential_id}",
        data=connector_id,
    )
