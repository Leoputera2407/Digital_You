import time
from sqlalchemy.orm import Session
from digital_twin.db.engine import  get_sqlalchemy_engine
from digital_twin.utils.logging import setup_logger
from digital_twin.background.utils import create_indexing_jobs, run_indexing_jobs

logger = setup_logger()

def batch_update() -> None:
    engine = get_sqlalchemy_engine()
    start = time.time()
    logger.info(f"Running update, current time: {time.ctime(start)}")
    try:
        with Session(engine, expire_on_commit=False) as db_session:
            create_indexing_jobs(db_session, is_daemon=False)
            run_indexing_jobs(db_session)
    except Exception as e:
        logger.exception(f"Failed to run update due to {e}")
    logger.info(f"Finished update, current time: {time.ctime(time.time())}")


if __name__ == "__main__":
    batch_update()
