import asyncio
import functools
from typing import TypeVar, Callable

T = TypeVar("T")

def async_timeout(seconds: int = 10):
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
        return wrapper
    return decorator
