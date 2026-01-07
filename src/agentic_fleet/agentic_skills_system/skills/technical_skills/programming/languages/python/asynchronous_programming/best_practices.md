## Best Practices

- Never use time.sleep() or blocking I/O (like requests) directly inside an async def; it freezes the entire event loop.
- Always prefer asyncio.run() for entry points to ensure proper cleanup of the event loop and generators.
- Use asyncio.create_task() to start background tasks without immediately awaiting them, but maintain a reference to the task to prevent garbage collection.
- Utilize asyncio.shield() when a specific operation must complete even if the surrounding context is cancelled.
- Always handle asyncio.CancelledError in critical sections to perform cleanup (e.g., closing file handles or database transactions).
- Use Semaphores to limit the number of concurrent tasks (e.g., rate-limiting API calls).