import argparse
import time
from uuid import UUID

from sqlalchemy.orm import Session

from digital_twin.background.utils import create_indexing_jobs, run_indexing_jobs
from digital_twin.db.engine import get_sqlalchemy_engine
from digital_twin.utils.logging import setup_logger

logger = setup_logger()


def batch_update(organization_id: UUID | None = None) -> None:
    engine = get_sqlalchemy_engine()
    start = time.time()
    logger.info(f"Running update, current time: {time.ctime(start)}")
    try:
        with Session(engine, expire_on_commit=False) as db_session:
            create_indexing_jobs(db_session, is_daemon=False, organization_id=organization_id)
            run_indexing_jobs(db_session, organization_id=organization_id)
    except Exception as e:
        logger.exception(f"Failed to run update due to {e}")
    logger.info(f"Finished update, current time: {time.ctime(time.time())}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch update for digital twin.")
    parser.add_argument("--organization_id", type=str, help="The UUID of the organization.")
    args = parser.parse_args()

    organization_id = UUID(args.organization_id) if args.organization_id else None
    batch_update(organization_id=organization_id)
