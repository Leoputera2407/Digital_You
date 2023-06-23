from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from digital_twin.db.connectors.connectors import fetch_connector_by_id
from digital_twin.db.connectors.credentials import fetch_credential_by_id
from digital_twin.db.model import (
    ConnectorCredentialPair,
    IndexingStatus,
    User,
)
from digital_twin.server.model import StatusResponse
from digital_twin.utils.logging import setup_logger, log_sqlalchemy_error

logger = setup_logger()

@log_sqlalchemy_error(logger)
def get_connector_credential_pairs(
    db_session: Session, include_disabled: bool = True
) -> list[ConnectorCredentialPair]:
    stmt = select(ConnectorCredentialPair)
    if not include_disabled:
        stmt = stmt.where(ConnectorCredentialPair.connector.disabled == False)
    results = db_session.scalars(stmt)
    return list(results.all())

@log_sqlalchemy_error(logger)
def get_connector_credential_pair(
    connector_id: int,
    credential_id: int,
    db_session: Session,
) -> ConnectorCredentialPair | None:
    stmt = select(ConnectorCredentialPair)
    stmt = stmt.where(ConnectorCredentialPair.connector_id == connector_id)
    stmt = stmt.where(ConnectorCredentialPair.credential_id == credential_id)
    result = db_session.execute(stmt)
    return result.scalar_one_or_none()

@log_sqlalchemy_error(logger)
def update_connector_credential_pair(
    connector_id: int,
    credential_id: int,
    attempt_status: IndexingStatus,
    net_docs: int | None,
    db_session: Session,
) -> bool:
    try:
        cc_pair = get_connector_credential_pair(connector_id, credential_id, db_session)
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

@log_sqlalchemy_error(logger)
def add_credential_to_connector(
    connector_id: int,
    credential_id: int,
    user: User,
    db_session: Session,
) -> StatusResponse[int]:
    connector = fetch_connector_by_id(connector_id, db_session)
    credential = fetch_credential_by_id(credential_id, user, db_session)

    if connector is None:
        raise HTTPException(status_code=404, detail="Connector does not exist")

    if credential is None:
        raise HTTPException(
            status_code=401,
            detail="Credential does not exist or does not belong to user",
        )

    existing_association = (
        db_session.query(ConnectorCredentialPair)
        .filter(
            ConnectorCredentialPair.connector_id == connector_id,
            ConnectorCredentialPair.credential_id == credential_id,
        )
        .one_or_none()
    )
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
    db_session.commit()

    return StatusResponse(
        success=True,
        message=f"New Credential {credential_id} added to Connector",
        data=connector_id,
    )

@log_sqlalchemy_error(logger)
def remove_credential_from_connector(
    connector_id: int,
    credential_id: int,
    user: User,
    db_session: Session,
) -> StatusResponse[int]:
    connector = fetch_connector_by_id(connector_id, db_session)
    credential = fetch_credential_by_id(credential_id, user, db_session)

    if connector is None:
        raise HTTPException(status_code=404, detail="Connector does not exist")

    if credential is None:
        raise HTTPException(
            status_code=404,
            detail="Credential does not exist or does not belong to user",
        )

    association = (
        db_session.query(ConnectorCredentialPair)
        .filter(
            ConnectorCredentialPair.connector_id == connector_id,
            ConnectorCredentialPair.credential_id == credential_id,
        )
        .one_or_none()
    )

    if association is not None:
        db_session.delete(association)
        db_session.commit()
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
