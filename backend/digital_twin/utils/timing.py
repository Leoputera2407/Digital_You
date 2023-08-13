import asyncio
import time
from collections.abc import Callable
from datetime import datetime
from functools import wraps
from typing import Any, TypeVar, cast

from digital_twin.utils.logging import setup_logger

logger = setup_logger()

F = TypeVar("F", bound=Callable)


def log_function_time(
    func_name: str | None = None,
) -> Callable[[F], F]:
    """Build a timing wrapper for a function. Logs how long the function took to run.
    Use like:

    @log_function_time()
    def my_func():
        ...
    """

    def timing_wrapper(func: F) -> F:
        if asyncio.iscoroutinefunction(func):

            @wraps(func)
            async def wrapped_func(*args: Any, **kwargs: Any) -> Any:
                start_time = time.time()
                result = await func(*args, **kwargs)
                logger.info(f"{func_name or func.__name__} took {time.time() - start_time} seconds")
                return result

        else:

            @wraps(func)
            def wrapped_func(*args: Any, **kwargs: Any) -> Any:
                start_time = time.time()
                result = func(*args, **kwargs)
                logger.info(f"{func_name or func.__name__} took {time.time() - start_time} seconds")
                return result

        return cast(F, wrapped_func)

    return timing_wrapper


def format_timestamp(timestamp) -> str:
    if timestamp is not None:
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
    return ""
