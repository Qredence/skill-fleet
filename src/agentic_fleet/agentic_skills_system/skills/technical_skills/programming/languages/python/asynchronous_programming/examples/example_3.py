import asyncio
import time


def blocking_io():
    time.sleep(2)  # High-latency blocking call
    return "Done"


async def main():
    loop = asyncio.get_running_loop()
    # 1. Run in default thread pool executor
    result = await loop.run_in_executor(None, blocking_io)
    print(f"Blocking result: {result}")


asyncio.run(main())
