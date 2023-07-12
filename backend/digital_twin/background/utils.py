
import time
from sqlalchemy.orm import Session

from digital_twin.connectors.factory import instantiate_connector, CONNECTOR_MAP
from digital_twin.connectors.interfaces import LoadConnector, PollConnector
from digital_twin.connectors.model import InputType

from digital_twin.db.connectors.connectors import (
    fetch_connectors, 
    backend_disable_connector,
    update_connector,
)
from digital_twin.db.connectors.credentials import backend_update_credential_json
from digital_twin.db.engine import get_db_current_time, get_sqlalchemy_engine
from digital_twin.db.connectors.connector_credential_pair import (
    backend_update_connector_credential_pair
)
from digital_twin.db.connectors.index_attempt import (
    create_index_attempt,
    get_inprogress_index_attempts,
    get_last_successful_attempt,
    get_last_successful_attempt_start_time,
    get_not_started_index_attempts,
    mark_attempt_failed,
    mark_attempt_in_progress,
    mark_attempt_succeeded,
)
from digital_twin.db.model import Connector, IndexAttempt, IndexingStatus
from digital_twin.db.user import get_qdrant_collection_by_user_id, get_typesense_collection_by_user_id
from digital_twin.indexdb.qdrant.store import QdrantVectorDB
from digital_twin.indexdb.typesense.store import TypesenseIndex
from digital_twin.utils.indexing_pipeline import build_indexing_pipeline
from digital_twin.utils.logging import setup_logger


logger = setup_logger()
def create_collections_if_not_exist(
        qdrant_collection_name: str, 
        typesense_collection_name: str
) -> None:
    from digital_twin.indexdb.qdrant.indexing import (
        create_collection,
        list_collections,
    )
    from digital_twin.indexdb.typesense.store import (
        check_typesense_collection_exist,
        create_typesense_collection,
    )
    
    if qdrant_collection_name not in {
        collection.name for collection in list_collections().collections
    }:
        logger.info(
            f"Creating collection with name: {qdrant_collection_name}"
        )
        create_collection(collection_name=qdrant_collection_name)
    
    if not check_typesense_collection_exist(typesense_collection_name):
        logger.info(
            f"Creating Typesense collection with name: {typesense_collection_name}"
        )
        create_typesense_collection(collection_name=typesense_collection_name)

def should_change_to_polling_connector(
    connector: Connector
) -> bool:
    connector_class = CONNECTOR_MAP[connector.source]
    if issubclass(connector_class, PollConnector):
        return True
    else:
        return False

def should_create_new_indexing(
    connector: Connector, last_index: IndexAttempt | None, db_session: Session
) -> bool:
    if connector.refresh_freq is None:
        return False
    if not last_index:
        return True
    current_db_time = get_db_current_time(db_session)
    time_since_index = current_db_time - last_index.updated_at
    return time_since_index.total_seconds() >= connector.refresh_freq

def create_indexing_jobs(db_session: Session, is_daemon:bool=True) -> None:
    connectors = fetch_connectors(db_session, disabled_status=False)
    for connector in connectors:
        in_progress_indexing_attempts = get_inprogress_index_attempts(
            connector.id, db_session
        )
        if in_progress_indexing_attempts:
            logger.error("Found incomplete indexing attempts")

        # Currently single threaded so any still in-progress must have errored
        for attempt in in_progress_indexing_attempts:
            logger.warning(
                f"Marking in-progress attempt 'connector: {attempt.connector_id}, "
                f"credential: {attempt.credential_id}' as failed"
            )
            mark_attempt_failed(attempt, db_session)
            if attempt.connector_id and attempt.credential_id:
                backend_update_connector_credential_pair(
                    connector_id=attempt.connector_id,
                    credential_id=attempt.credential_id,
                    attempt_status=IndexingStatus.FAILED,
                    net_docs=None,
                    db_session=db_session,
                )

        for association in connector.credentials:
            credential = association.credential

            last_successful_attempt = get_last_successful_attempt(
                connector.id, credential.id, db_session
            )
            if is_daemon and not should_create_new_indexing(
                connector, last_successful_attempt, db_session
            ):
                continue

            # If Polling exists, we should change to polling connector
            if should_change_to_polling_connector(
                connector
            ):
                new_connector = Connector(
                    name=connector.name,
                    source=connector.source,
                    connector_specific_config=connector.connector_specific_config,
                    input_type=InputType.POLL,
                    refresh_freq=connector.refresh_freq,
                    disabled=connector.disabled,
                    organization_id=connector.organization_id
                )
                updated_connector = update_connector(
                    connector_id=connector.id,
                    connector_data=new_connector,
                    organization_id=connector.organization_id,
                    db_session=db_session,
                )
                if updated_connector is None:
                    logger.error(
                        f"Failed to update connector: {connector.id} to polling connector, continuing "
                        "as load all connector"
                    )
                    continue
                
            create_index_attempt(connector.id, credential.id, db_session)

            backend_update_connector_credential_pair(
                connector_id=connector.id,
                credential_id=credential.id,
                attempt_status=IndexingStatus.NOT_STARTED,
                net_docs=None,
                db_session=db_session,
            )


def run_indexing_jobs(db_session: Session) -> None:
    new_indexing_attempts = get_not_started_index_attempts(db_session)
    logger.info(f"Found {len(new_indexing_attempts)} new indexing tasks.")
    for attempt in new_indexing_attempts:
        logger.info(
            f"Starting new indexing attempt for connector: '{attempt.connector.name}', "
            f"with config: '{attempt.connector.connector_specific_config}', and "
            f"with credentials: '{[c.credential_id for c in attempt.connector.credentials]}'"
        )
        mark_attempt_in_progress(attempt, db_session)

        db_connector = attempt.connector
        db_credential = attempt.credential
        task = db_connector.input_type

        org_qdrant_collection = get_qdrant_collection_by_user_id(
            db_session, 
            db_credential.user_id,
            db_credential.organization_id,
        )
        org_typesense_collection = get_typesense_collection_by_user_id(
            db_session, 
            db_credential.user_id,
            db_credential.organization_id,
        )

        org_indexing_pipeline = build_indexing_pipeline(
            vectordb=QdrantVectorDB(collection=org_qdrant_collection),
            keyword_index=TypesenseIndex(collection=org_typesense_collection),
        )   

        backend_update_connector_credential_pair(
            connector_id=db_connector.id,
            credential_id=db_credential.id,
            attempt_status=IndexingStatus.IN_PROGRESS,
            net_docs=None,
            db_session=db_session,
        )

        try:
            runnable_connector, new_credential_json = instantiate_connector(
                db_connector.source,
                task,
                db_connector.connector_specific_config,
                db_credential.credential_json,
            )
            if new_credential_json is not None:
                backend_update_credential_json(
                    db_credential, new_credential_json, db_session
                )
        except Exception as e:
            logger.exception(f"Unable to instantiate connector due to {e}")
            backend_disable_connector(db_connector.id, db_session)
            continue

        net_doc_change = 0
        try:
            if task == InputType.LOAD_STATE:
                assert isinstance(runnable_connector, LoadConnector)
                doc_batch_generator = runnable_connector.load_from_state()

            elif task == InputType.POLL:
                assert isinstance(runnable_connector, PollConnector)
                if attempt.connector_id is None or attempt.credential_id is None:
                    raise ValueError(
                        f"Polling attempt {attempt.id} is missing connector_id or credential_id, "
                        f"can't fetch time range."
                    )
                last_run_time = get_last_successful_attempt_start_time(
                    attempt.connector_id, attempt.credential_id, db_session
                )
                doc_batch_generator = runnable_connector.poll_source(
                    last_run_time, time.time()
                )

            else:
                # Event types cannot be handled by a background type, leave these untouched
                continue

            create_collections_if_not_exist(
                qdrant_collection_name=org_qdrant_collection,
                typesense_collection_name=org_typesense_collection,
            )

            document_ids: list[str] = []
            for doc_batch in doc_batch_generator:
                index_user_id = (
                    None if db_credential.public_doc else db_credential.user_id
                )
                net_doc_change += org_indexing_pipeline(
                    documents=doc_batch, user_id=index_user_id
                )
                document_ids.extend([doc.id for doc in doc_batch])

            mark_attempt_succeeded(attempt, document_ids, db_session)
            backend_update_connector_credential_pair(
                connector_id=db_connector.id,
                credential_id=db_credential.id,
                attempt_status=IndexingStatus.SUCCESS,
                net_docs=net_doc_change,
                db_session=db_session,
            )

            logger.info(f"Indexed {len(document_ids)} documents")
           
        except Exception as e:
            logger.exception(f"Indexing job with id {attempt.id} failed due to {e}")
            mark_attempt_failed(attempt, db_session, failure_reason=str(e))
            backend_update_connector_credential_pair(
                connector_id=db_connector.id,
                credential_id=db_credential.id,
                attempt_status=IndexingStatus.FAILED,
                net_docs=net_doc_change,
                db_session=db_session,
            )