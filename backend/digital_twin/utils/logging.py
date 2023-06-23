import logging
import traceback
from logging import Logger
from functools import wraps
from sqlalchemy.exc import SQLAlchemyError

def setup_logger(
    name: str = __name__, log_level: int = logging.INFO
) -> Logger:
    logger = logging.getLogger(name)

    # If the logger already has handlers, assume it was already configured and return it.
    if logger.handlers:
        return logger

    logger.setLevel(log_level)

    formatter = logging.Formatter(
        "%(asctime)s %(filename)20s%(lineno)4s : %(message)s",
        datefmt="%m/%d/%Y %I:%M:%S %p",
    )

    handler = logging.StreamHandler()
    handler.setLevel(log_level)
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


def log_sqlalchemy_error(logger):
    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except SQLAlchemyError as e:
                logger.error(f"SQLAlchemy error in {func.__name__}: {str(e)}")
                logger.debug(f"Full traceback: {traceback.format_exc()}")
                raise e
            except Exception as e:
                logger.error(f"SQLAlchemy error in {func.__name__}: {str(e)}")
                raise e
        return wrapped
    return decorator


def async_log_sqlalchemy_error(logger):
    def decorator(func):
        @wraps(func)
        async def wrapped(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except SQLAlchemyError as e:
                logger.error(f"SQLAlchemy error in {func.__name__}: {str(e)}")
                logger.debug(f"Full traceback: {traceback.format_exc()}")
                raise e
            except Exception as e:
                logger.error(f"General error in {func.__name__}: {str(e)}")
                raise e
        return wrapped
    return decorator