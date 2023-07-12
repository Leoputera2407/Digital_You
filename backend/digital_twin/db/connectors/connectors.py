from typing import cast
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session, aliased, joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from digital_twin.config.constants import DocumentSource
from digital_twin.connectors.model import InputType
from digital_twin.db.model import Connector, IndexAttempt
from digital_twin.server.model import (
    ConnectorBase,
    ObjectCreationIdResponse,
    StatusResponse,
)

from digital_twin.utils.logging import (
     setup_logger,
    log_sqlalchemy_error,
    async_log_sqlalchemy_error,
)

logger = setup_logger()

@log_sqlalchemy_error(logger)
def fetch_connectors(
    db_session: Session,
    sources: list[DocumentSource] | None = None,
    input_types: list[InputType] | None = None,
    organization_id: UUID | None = None,
    disabled_status: bool | None = None,
) -> list[Connector]:
    stmt = select(Connector)
    if sources is not None:
        stmt = stmt.where(Connector.source.in_(sources))
    if input_types is not None:
        stmt = stmt.where(Connector.input_type.in_(input_types))
    if disabled_status is not None:
        stmt = stmt.where(Connector.disabled == disabled_status)
    if organization_id is not None:
        stmt = stmt.where(Connector.organization_id == organization_id)
    results = db_session.scalars(stmt)
    return list(results.all())

@async_log_sqlalchemy_error(logger)
async def async_fetch_connectors(
    db_session: AsyncSession,
    sources: list[DocumentSource] | None = None,
    input_types: list[InputType] | None = None,
    organization_id: UUID | None = None,
    disabled_status: bool | None = None,
) -> list[Connector]:
    stmt = select(Connector).options(joinedload(Connector.credentials))
    if sources is not None:
        stmt = stmt.where(Connector.source.in_(sources))
    if input_types is not None:
        stmt = stmt.where(Connector.input_type.in_(input_types))
    if disabled_status is not None:
        stmt = stmt.where(Connector.disabled == disabled_status)
    if organization_id is not None:
        stmt = stmt.where(Connector.organization_id == organization_id)
    results = await db_session.scalars(stmt)
    return list(results.unique().all())

@log_sqlalchemy_error(logger)
def connector_by_name_exists_in_org(
    connector_name: str, 
    organization_id: UUID,
    db_session: Session,
) -> bool:
    stmt = select(Connector).where((Connector.name == connector_name) & (Connector.organization_id == organization_id))
    result = db_session.execute(stmt)
    connector = result.scalar_one_or_none()
    return connector is not None

@async_log_sqlalchemy_error(logger)
async def async_connector_by_name_exists_in_org(
    connector_name: str, 
    organization_id: UUID,
    db_session: AsyncSession,
) -> bool:
    stmt = select(Connector).where((Connector.name == connector_name) & (Connector.organization_id == organization_id))
    result = await db_session.execute(stmt)
    connector = result.scalar_one_or_none()
    return connector is not None


@log_sqlalchemy_error(logger)
def fetch_connector_by_id_and_org(
    connector_id: int, 
    organization_id: UUID | None,
    db_session: Session,
) -> Connector | None:
    stmt = select(Connector).where(Connector.id == connector_id)

    if organization_id is not None:
        stmt = stmt.where(Connector.organization_id == organization_id)

    result = db_session.execute(stmt)
    connector = result.scalar_one_or_none()
    return connector

@async_log_sqlalchemy_error(logger)
async def async_fetch_connector_by_id_and_org(
    connector_id: int, 
    organization_id: UUID | None,
    db_session: AsyncSession,
) -> Connector | None:
    try:
        stmt = select(Connector).options(joinedload(Connector.credentials)).where(Connector.id == connector_id)

        if organization_id is not None:
            stmt = stmt.where(Connector.organization_id == organization_id)

        result = await db_session.execute(stmt)
        connector = result.unique().scalars().first()
        return connector

    except Exception as e:
        logger.error(f"Error executing SQL query: {e}")
        return None
    
@log_sqlalchemy_error(logger)
def create_connector(
    connector_data: ConnectorBase,
    organization_id: UUID,
    db_session: Session,
) -> ObjectCreationIdResponse:
    if organization_id is None:
        raise ValueError("Organization ID must be provided.")
    
    if connector_by_name_exists_in_org(
        connector_data.name, 
        organization_id,
        db_session
    ):
        raise ValueError(
            "Connector by this name already exists for this org, duplicate naming not allowed."
        )

    connector = Connector(
        name=connector_data.name,
        source=connector_data.source,
        input_type=connector_data.input_type,
        connector_specific_config=connector_data.connector_specific_config,
        refresh_freq=connector_data.refresh_freq,
        disabled=connector_data.disabled,
        organization_id=organization_id,
    )
    db_session.add(connector)
    db_session.commit()

    return ObjectCreationIdResponse(id=connector.id)

@async_log_sqlalchemy_error(logger)
async def async_create_connector(
    connector_data: ConnectorBase,
    organization_id: UUID,
    db_session: AsyncSession,
) -> ObjectCreationIdResponse:
    if organization_id is None:
        raise ValueError("Organization ID must be provided.")
    
    if await async_connector_by_name_exists_in_org(
        connector_data.name, 
        organization_id,
        db_session
    ):
        raise ValueError(
            "Connector by this name already exists for this org, duplicate naming not allowed."
        )

    connector = Connector(
        name=connector_data.name,
        source=connector_data.source,
        input_type=connector_data.input_type,
        connector_specific_config=connector_data.connector_specific_config,
        refresh_freq=connector_data.refresh_freq,
        disabled=connector_data.disabled,
        organization_id=organization_id,
    )
    db_session.add(connector)
    await db_session.commit()

    return ObjectCreationIdResponse(id=connector.id)


@log_sqlalchemy_error(logger)
def update_connector(
    connector_id: int,
    connector_data: ConnectorBase,
    organization_id: UUID,
    db_session: Session,
) -> Connector | None:
    if organization_id is None:
        raise ValueError("Organization ID must be provided.")
    connector = fetch_connector_by_id_and_org(
        connector_id, 
        organization_id,
        db_session
    )
    if connector is None:
        return None

    if connector_data.name != connector.name and connector_by_name_exists_in_org(
        connector_data.name, 
        organization_id,
        db_session,
    ):
        raise ValueError(
            "Connector by this name already exists for this org, duplicate naming not allowed."
        )

    connector.name = connector_data.name
    connector.source = connector_data.source
    connector.input_type = connector_data.input_type
    connector.connector_specific_config = connector_data.connector_specific_config
    connector.refresh_freq = connector_data.refresh_freq
    connector.disabled = connector_data.disabled
    connector.organization_id = organization_id

    db_session.commit()
    return connector

@async_log_sqlalchemy_error(logger)
async def async_update_connector(
    connector_id: int,
    connector_data: ConnectorBase,
    organization_id: UUID,
    db_session: AsyncSession,
) -> Connector | None:
    if organization_id is None:
        raise ValueError("Organization ID must be provided.")
    connector = await async_fetch_connector_by_id_and_org(
        connector_id, 
        organization_id,
        db_session
    )
    if connector is None:
        return None

    if connector_data.name != connector.name and await async_connector_by_name_exists_in_org(
        connector_data.name, 
        organization_id,
        db_session,
    ):
        raise ValueError(
            "Connector by this name already exists for this org, duplicate naming not allowed."
        )

    connector.name = connector_data.name
    connector.source = connector_data.source
    connector.input_type = connector_data.input_type
    connector.connector_specific_config = connector_data.connector_specific_config
    connector.refresh_freq = connector_data.refresh_freq
    connector.disabled = connector_data.disabled
    connector.organization_id = organization_id

    await db_session.commit()
    await db_session.refresh(connector)

    return connector


@log_sqlalchemy_error(logger)
def disable_connector(
    connector_id: int,
    organization_id: UUID,
    db_session: Session,
) -> StatusResponse[int]:
    if organization_id is None:
        raise HTTPException(status_code=400, detail="Organization ID must be provided.")
    connector = fetch_connector_by_id_and_org(
        connector_id, 
        organization_id,
        db_session
    )
    if connector is None:
        raise HTTPException(status_code=404, detail="Connector does not exist")

    connector.disabled = True
    db_session.commit()
    return StatusResponse(
        success=True, message="Connector deleted successfully", data=connector_id
    )

@log_sqlalchemy_error(logger)
def backend_disable_connector(
    connector_id: int,
    db_session: Session,
) -> StatusResponse[int]:
    """
    This should only be used in the backend, as
    we want to disable regardless of org_id
    """
    connector = fetch_connector_by_id_and_org(
        connector_id, 
        organization_id = None,
        db_session = db_session,
    )
    if connector is None:
        raise HTTPException(status_code=404, detail="Connector does not exist")

    connector.disabled = True
    db_session.commit()
    return StatusResponse(
        success=True, message="Connector deleted successfully", data=connector_id
    )


@log_sqlalchemy_error(logger)
def delete_connector(
    connector_id: int,
    organization_id: UUID,
    db_session: Session,
) -> StatusResponse[int]:
    """Currently unused due to foreign key restriction from IndexAttempt
    Use disable_connector instead"""
    connector = fetch_connector_by_id_and_org(
        connector_id, 
        organization_id,
        db_session
    )
    if connector is None:
        return StatusResponse(
            success=True, message="Connector was already deleted", data=connector_id
        )

    db_session.delete(connector)
    db_session.commit()
    return StatusResponse(
        success=True, message="Connector deleted successfully", data=connector_id
    )

@async_log_sqlalchemy_error(logger)
async def async_delete_connector(
    connector_id: int,
    organization_id: UUID,
    db_session: AsyncSession,
) -> StatusResponse[int]:
    """Currently unused due to foreign key restriction from IndexAttempt
    Use disable_connector instead"""
    connector = await async_fetch_connector_by_id_and_org(
        connector_id, 
        organization_id,
        db_session
    )
    if connector is None:
        return StatusResponse(
            success=True, message="Connector was already deleted", data=connector_id
        )

    await db_session.delete(connector)
    await db_session.commit()
    return StatusResponse(
        success=True, message="Connector deleted successfully", data=connector_id
    )

@log_sqlalchemy_error(logger)
def get_connector_credential_ids(
    connector_id: int,
    organization_id: UUID,
    db_session: Session,
) -> list[int]:
    connector = fetch_connector_by_id_and_org(
        connector_id, 
        organization_id,
        db_session
    )
    if connector is None:
        raise ValueError(f"Connector by id {connector_id} does not exist")

    return [association.credential.id for association in connector.credentials]

@async_log_sqlalchemy_error(logger)
async def async_get_connector_credential_ids(
    connector_id: int,
    organization_id: UUID,
    db_session: AsyncSession,
) -> list[int]:
    connector = await async_fetch_connector_by_id_and_org(
        connector_id, 
        organization_id,
        db_session
    )
    if connector is None:
        raise ValueError(f"Connector by id {connector_id} does not exist")

    return [association.credential.id for association in connector.credentials]

@log_sqlalchemy_error(logger)
def fetch_latest_index_attempt_by_connector(
    db_session: Session,
    organization_id: UUID,
    source: DocumentSource | None = None,
) -> list[IndexAttempt]:
    latest_index_attempts: list[IndexAttempt] = []
    if organization_id is None:
        raise ValueError("Organization ID must be provided.")

    if source:
        connectors = fetch_connectors(
            db_session, 
            sources=[source], 
            organization_id=organization_id,
            disabled_status=False,
        )
    else:
        connectors = fetch_connectors(
            db_session, 
            organization_id=organization_id,
            disabled_status=False
        )

    if not connectors:
        return []

    for connector in connectors:
        latest_index_attempt = (
            db_session.query(IndexAttempt)
            .filter(IndexAttempt.connector_id == connector.id)
            .order_by(IndexAttempt.updated_at.desc())
            .first()
        )

        if latest_index_attempt is not None:
            latest_index_attempts.append(latest_index_attempt)

    return latest_index_attempts

@log_sqlalchemy_error(logger)
def fetch_latest_index_attempts_by_status(
    db_session: Session,
    organization_id: UUID,
) -> list[IndexAttempt]:
    subquery = (
        db_session.query(
            IndexAttempt.connector_id,
            IndexAttempt.credential_id,
            IndexAttempt.status,
            func.max(IndexAttempt.updated_at).label("updated_at"),
        )
        .join(IndexAttempt.connector)
        .filter(Connector.organization_id == organization_id)
        .group_by(IndexAttempt.connector_id)
        .group_by(IndexAttempt.credential_id)
        .group_by(IndexAttempt.status)
        .subquery()
    )

    alias = aliased(IndexAttempt, subquery)

    query = db_session.query(IndexAttempt).join(
        alias,
        and_(
            IndexAttempt.connector_id == alias.connector_id,
            IndexAttempt.credential_id == alias.credential_id,
            IndexAttempt.status == alias.status,
            IndexAttempt.updated_at == alias.updated_at,
        ),
    )
    query = query.options(joinedload(IndexAttempt.connector)).filter(
        Connector.organization_id == organization_id
    )

    return cast(list[IndexAttempt], query.all())