import asyncio
from collections.abc import Callable
from typing import Any, TypeVar
_T = TypeVar("_T")
import concurrent.futures

def async_func_wrapper(target, *args: Any):
    loop = asyncio.new_event_loop()
    results = loop.run_until_complete(target(*args))
    loop.close()
    return results

def async_add_executor_job(
    target: Callable[..., _T],
    *args: Any,
) -> asyncio.Future[_T]:
    """Add an executor job from within the event loop."""
    loop = asyncio.new_event_loop()
    with concurrent.futures.ProcessPoolExecutor() as pool:
        return loop.run_in_executor(pool, async_func_wrapper, *[target, *args])

# async def _arun(self, 
#     loop = asyncio.get_running_loop()
#     return await async_add_executor_job(loop, tasks, get_stock_performance, ticker, days)
