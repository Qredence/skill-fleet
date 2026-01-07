### Composition Patterns

- **Web Frameworks (FastAPI/Sanic)**: This skill provides the 'engine' for modern Python web servers. Asyncio handles the request/response cycle, allowing the web framework to scale to thousands of concurrent users.
- **Network Programming**: When building custom TCP/UDP protocols, use `asyncio.Protocol` or `asyncio.Streams`. This skill allows for multiplexing connections efficiently without thread-per-connection overhead.
- **Data Pipelines**: Integrate `asyncio.Queue` with `async_iterators` to create streaming data processors that handle ingestion, transformation, and storage concurrently.
- **Database Access**: Pair with `asyncpg` or `motor` (MongoDB). Ensure that all database drivers used are native async drivers to avoid blocking the loop.

### Transitioning from Sync to Async
When integrating with existing synchronous codebases, identify I/O bottlenecks first. Introduce `asyncio` at the edges (Network/Disk) and use `run_in_executor` for existing business logic until it can be refactored to native coroutines.