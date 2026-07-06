"""Async retry decorator with exponential backoff"""
import asyncio
import functools
import logging

logger = logging.getLogger(__name__)


def async_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
):
    """Decorator that retries an async function with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts before giving up.
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay in seconds.
        backoff: Multiplier for delay after each attempt.
        exceptions: Tuple of exception types to catch and retry on.
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            delay = base_delay
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as exc:
                    last_exception = exc
                    if attempt == max_attempts:
                        logger.error(
                            "All %d attempts failed for %s: %s",
                            max_attempts, func.__name__, exc,
                        )
                        raise
                    logger.warning(
                        "Attempt %d/%d failed for %s: %s. Retrying in %.1fs...",
                        attempt, max_attempts, func.__name__, exc, delay,
                    )
                    await asyncio.sleep(delay)
                    delay = min(delay * backoff, max_delay)
            raise RuntimeError("Unreachable") from last_exception
        return wrapper
    return decorator
