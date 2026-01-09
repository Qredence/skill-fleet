import asyncio


async def slow_operation():
    try:
        await asyncio.sleep(10)
    except asyncio.CancelledError:
        print("Clean up after cancellation")
        raise


async def main():
    try:
        await asyncio.wait_for(slow_operation(), timeout=2.0)
    except TimeoutError:
        print("Operation timed out!")


asyncio.run(main())
