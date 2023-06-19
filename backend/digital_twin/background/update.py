import time
from dateutil import parser

from digital_twin.connectors.factory import instantiate_connector
from digital_twin.connectors.interfaces import LoadConnector, PollConnector
from digital_twin.connectors.model import InputType

from digital_twin.db.connectors.connectors import fetch_connectors, disable_connector
from digital_twin.db.connectors.credentials import update_credential_json
from digital_twin.db.connectors.index_attempt import (
    create_index_attempt,
    get_inprogress_index_attempts,
    get_last_finished_attempt,
    get_not_started_index_attempts,
    mark_attempt_failed,
    mark_attempt_in_progress,
    mark_attempt_succeeded,
)
from digital_twin.vectordb.qdrant.indexing import list_collections, create_collection
from digital_twin.db.model import Connector, IndexAttempt
from digital_twin.db.connectors.connectors import get_connector_credentials, fetch_connector_by_id, fetch_credential_by_id
from digital_twin.db.user import get_qdrant_collection_for_user
from digital_twin.db.admin import get_db_current_time
from digital_twin.utils.indexing_pipeline import build_indexing_pipeline
from digital_twin.utils.logging import setup_logger


logger = setup_logger()


def should_create_new_indexing(
    connector: Connector, 
    last_index: IndexAttempt | None,
) -> bool:
    if connector.refresh_freq is None:
        return False
    if not last_index:
        return True
    current_db_time_str = get_db_current_time()
    current_db_time = parser.parse(current_db_time_str) 
    last_index_time = parser.parse(last_index.updated_at) 
    time_since_index = (
        current_db_time - last_index_time
     ) # Maybe better to do time created
    return time_since_index.total_seconds() >= connector.refresh_freq


def create_indexing_jobs() -> None:
    # Get all connectors as long as it's not disabled
    connectors = fetch_connectors(disabled_status=False)
    for connector in connectors:
        in_progress_indexing_attempts = get_inprogress_index_attempts(
            connector.id
        )
        if in_progress_indexing_attempts:
            logger.error("Found incomplete indexing attempts")

        # Currently single threaded so any still in-progress must have errored
        for attempt in in_progress_indexing_attempts:
            logger.warning(
                f"Marking in-progress attempt 'connector: {attempt.connector_id}, credential: {attempt.credential_id}' as failed"
            )
            mark_attempt_failed(attempt.id)

        last_finished_indexing_attempt = get_last_finished_attempt(connector.id)
        if not should_create_new_indexing(
            connector, last_finished_indexing_attempt
        ):
            continue
        
        for credential in get_connector_credentials(connector.user_id, connector.id):
            create_index_attempt(connector.id, credential.id, connector.user_id)


def run_indexing_jobs(last_run_time: float) -> None:
    indexing_pipeline = build_indexing_pipeline()

    new_indexing_attempts = get_not_started_index_attempts()
    logger.info(f"Found {len(new_indexing_attempts)} new indexing tasks.")
    for attempt in new_indexing_attempts:
        connector = fetch_connector_by_id(attempt.connector_id)
        credential = fetch_credential_by_id(attempt.credential_id)
        logger.info(
            f"Starting new indexing attempt for connector: '{connector.name}', "
            f"with config: '{connector.connector_specific_config}', and "
            f" with credential: '{credential.id}'"
        )
        mark_attempt_in_progress(attempt.id)
        task = connector.input_type

        # Make Qdrant Client if not made already
        try:
            qdrant_collection_id = get_qdrant_collection_for_user(credential.user_id)
            if not qdrant_collection_id:
                raise Exception("No Qdrant collection found for user")
            if qdrant_collection_id not in list_collections():
                create_collection(qdrant_collection_id)
                logger.info(f"Created Qdrant collection {qdrant_collection_id} for user {credential.user_id}")
        except Exception as e:
            logger.exception(f"Unable to create Qdrant Cluster due to {e}")
            continue

        try:
            runnable_connector, new_credential_json = instantiate_connector(
                connector.source,
                task,
                connector.connector_specific_config,
                credential.credential_json,
            )
            if new_credential_json is not None:
                update_credential_json(
                    credential.id, new_credential_json, credential.user_id
                )
        except Exception as e:
            logger.exception(f"Unable to instantiate connector due to {e}")
            disable_connector(connector.user_id, connector.id)
            continue

        try:
            if task == InputType.LOAD_STATE:
                assert isinstance(runnable_connector, LoadConnector)
                doc_batch_generator = runnable_connector.load_from_state()

            elif task == InputType.POLL:
                assert isinstance(runnable_connector, PollConnector)
                doc_batch_generator = runnable_connector.poll_source(
                    last_run_time, time.time()
                )

            else:
                # Event types cannot be handled by a background type, leave these untouched
                continue

            document_ids: list[str] = []
            for doc_batch in doc_batch_generator:
                indexing_pipeline(documents=doc_batch, user_id=credential.user_id)
                document_ids.extend([doc.id for doc in doc_batch])

            mark_attempt_succeeded(attempt.id, document_ids)

        except Exception as e:
            logger.exception(f"Indexing job with id {attempt.id} failed due to {e}")
            mark_attempt_failed(attempt.id, failure_reason=str(e))


def update_loop(delay: int = 10) -> None:
    last_run_time = 0.0
    while True:
        start = time.time()
        logger.info(f"Running update, current time: {time.ctime(start)}")
        try:
            create_indexing_jobs()
            # TODO failed poll jobs won't recover data from failed runs, should fix
            run_indexing_jobs(last_run_time)
        except Exception as e:
            logger.exception(f"Failed to run update due to {e}")
        sleep_time = delay - (time.time() - start)
        if sleep_time > 0:
            time.sleep(sleep_time)


if __name__ == "__main__":
    update_loop()
