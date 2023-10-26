import asyncio
from typing import Callable, Any

loop = asyncio.get_event_loop()

def async_add_executor_job(
    target: Callable, *args: Any
) -> asyncio.Future:
    """Add an executor job from within the event loop."""
    task = loop.run_in_executor(None, target, *args)
    return task

def run_me(arg1, arg2):
    return arg1 + arg2

async def main():
    result = await async_add_executor_job(run_me, 1, 3)
    print(result)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
