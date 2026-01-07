import asyncio


async def fetch_data(id):
    print(f"Task {id} starting...")
    await asyncio.sleep(1)  # Simulate I/O
    return f"Data {id}"


async def main():
    # Run tasks concurrently
    results = await asyncio.gather(fetch_data(1), fetch_data(2), fetch_data(3))
    print(f"Results: {results}")


if __name__ == "__main__":
    asyncio.run(main())
