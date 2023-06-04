import logging
from logging import Logger
from functools import wraps
from postgrest.exceptions import APIError


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


def log_supabase_api_error(logger):
    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except APIError as e:
                logger.error(f"API error in {func.__name__}: {e}")
                return None
        return wrapped
    return decorator
