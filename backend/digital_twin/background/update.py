import time

from sqlalchemy.orm import Session

from digital_twin.background.utils import create_indexing_jobs, run_indexing_jobs
from digital_twin.db.engine import get_sqlalchemy_engine
from digital_twin.utils.logging import setup_logger

logger = setup_logger()


def update_loop(delay: int = 10) -> None:
    engine = get_sqlalchemy_engine()
    while True:
        start = time.time()
        logger.info(f"Running update, current time: {time.ctime(start)}")
        try:
            with Session(engine, expire_on_commit=False) as db_session:
                create_indexing_jobs(db_session)
                run_indexing_jobs(db_session)
        except Exception as e:
            logger.exception(f"Failed to run update due to {e}")
        sleep_time = delay - (time.time() - start)
        if sleep_time > 0:
            time.sleep(sleep_time)


if __name__ == "__main__":
    update_loop()
