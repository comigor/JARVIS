import asyncio
from collections.abc import Callable
from typing import Any, TypeVar
_T = TypeVar("_T")

# Copied from HomeAssistant because I don't want to pass hass around everything
def async_add_executor_job(
    target: Callable[..., _T],
    *args: Any,
) -> asyncio.Future[_T]:
    """Add an executor job from within the event loop."""
    loop = asyncio.get_running_loop()
    return loop.run_in_executor(None, target, *args)
