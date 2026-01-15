#!/usr/bin/env python3
"""
Universal Memory - 3-line pattern for adding memory to any LLM agent

Drop-in replacement for cloud-based memory systems.
Works locally with no external dependencies.
"""

from typing import Optional, List, Dict, Any
from functools import wraps

# Import memory manager
from memory_manager import MemoryManager, ContextInjector


class MemoryContext:
    """
    Context manager for adding persistent memory to LLM agents.

    Usage:
        with MemoryContext(agent="my-agent"):
            response = openai.chat.completions.create(...)
    """

    _instances: Dict[str, "MemoryContext"] = {}

    def __init__(
        self,
        agent: str,
        memory: Optional[List[Dict[str, str]]] = None,
        capture_only: bool = False,
        storage_type: str = "sqlite",
        storage_path: Optional[str] = None,
        memory_limit: int = 10000,
    ):
        """
        Initialize memory context.

        Args:
            agent: Unique agent identifier
            memory: Optional custom memory blocks
            capture_only: Save conversations without injecting context
            storage_type: "sqlite" or "json"
            storage_path: Custom storage path
            memory_limit: Max characters per agent
        """
        self.agent = agent
        self.memory_blocks = memory
        self.capture_only = capture_only
        self.storage_type = storage_type
        self.storage_path = storage_path
        self.memory_limit = memory_limit

        # Initialize memory manager
        self.manager = MemoryManager(
            agent=agent,
            storage_type=storage_type,
            storage_path=None if storage_path is None else None,  # Will use default
        )

        # Track current conversation
        self.current_conversation: List[Dict[str, Any]] = []
        self.in_context = False

    def __enter__(self):
        """Enter memory context and inject relevant context."""
        MemoryContext._instances[self.agent] = self
        self.in_context = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit memory context and save conversation."""
        self.in_context = False

        # Save conversation if there are messages
        if self.current_conversation:
            self.manager.save_conversation(
                messages=self.current_conversation, capture_only=self.capture_only
            )

        self.current_conversation = []
        return False

    @staticmethod
    def get_current(agent: str) -> Optional["MemoryContext"]:
        """Get the active MemoryContext for an agent."""
        return MemoryContext._instances.get(agent)


class AsyncMemoryContext(MemoryContext):
    """
    Async context manager for adding persistent memory to LLM agents.

    Usage:
        async with AsyncMemoryContext(agent="my-agent"):
            response = await claude.messages.create(...)
    """

    async def __aenter__(self):
        """Enter async memory context."""
        return self.__enter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async memory context."""
        return self.__exit__(exc_type, exc_val, exc_tb)


def inject_context(func):
    """
    Decorator to automatically inject context into LLM calls.

    Usage:
        @inject_context
        def chat(message: str, agent: str = "my-agent"):
            return openai.chat.completions.create(...)
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Extract agent from kwargs or use default
        agent_name = kwargs.pop("agent", None)

        if not agent_name:
            # Try to find agent from current MemoryContext
            for agent, ctx in MemoryContext._instances.items():
                if ctx.in_context:
                    agent_name = agent
                    break

        if not agent_name:
            return func(*args, **kwargs)

        # Get context if available
        ctx = MemoryContext._instances.get(agent_name)
        if not ctx or ctx.capture_only:
            return func(*args, **kwargs)

        # Get relevant context
        context = ctx.manager.get_context(limit=5, max_tokens=2000)

        if not context:
            return func(*args, **kwargs)

        # Inject context into function call
        if "messages" in kwargs:
            # Messages-based API (OpenAI, Claude)
            kwargs["messages"] = ContextInjector.inject_messages(kwargs["messages"], context)
        elif "prompt" in kwargs:
            # Prompt-based API (Gemini, completion)
            kwargs["prompt"] = ContextInjector.inject_context(kwargs["prompt"], context)
        else:
            # Try to inject into first string argument
            if args and isinstance(args[0], str):
                args = (ContextInjector.inject_context(args[0], context),) + args[1:]

        return func(*args, **kwargs)

    return wrapper


def track_conversation(agent: str):
    """
    Decorator to track conversations for memory.

    Usage:
        @track_conversation(agent="my-agent")
        def chat(message: str):
            return llm_client.generate(message)
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get context
            ctx = MemoryContext._instances.get(agent)

            if not ctx:
                return func(*args, **kwargs)

            # Extract user message
            user_message = None

            # Try to extract from messages
            if "messages" in kwargs and kwargs["messages"]:
                last_msg = kwargs["messages"][-1]
                user_message = last_msg.get("content", str(last_msg))
            elif "prompt" in kwargs:
                user_message = kwargs["prompt"]
            elif args and isinstance(args[0], str):
                user_message = args[0]

            # Track user message
            if user_message:
                ctx.current_conversation.append({"role": "user", "content": user_message})

            # Execute function
            try:
                result = func(*args, **kwargs)

                # Extract assistant response
                assistant_message = None

                if hasattr(result, "choices"):  # OpenAI-like response
                    if hasattr(result.choices[0], "message"):
                        assistant_message = result.choices[0].message.content
                elif hasattr(result, "content"):  # Claude-like response
                    if isinstance(result.content, list):
                        assistant_message = result.content[0].text
                    else:
                        assistant_message = result.content
                elif hasattr(result, "text"):  # Gemini-like response
                    assistant_message = result.text
                elif isinstance(result, str):  # String response
                    assistant_message = result

                # Track assistant response
                if assistant_message:
                    ctx.current_conversation.append(
                        {"role": "assistant", "content": assistant_message}
                    )

                return result

            except Exception as e:
                # Track error as assistant message
                ctx.current_conversation.append(
                    {"role": "assistant", "content": f"Error: {str(e)}"}
                )
                raise

        return wrapper

    return decorator


def learning(agent: str, **kwargs):
    """
    Convenience function for quick memory integration.

    Usage:
        with learning(agent="my-agent"):
            response = llm_call(...)
    """
    return MemoryContext(agent=agent, **kwargs)


def learning_async(agent: str, **kwargs):
    """
    Convenience function for async memory integration.

    Usage:
        async with learning_async(agent="my-agent"):
            response = await llm_call(...)
    """
    return AsyncMemoryContext(agent=agent, **kwargs)


# Convenience aliases
memory = learning
memory_async = learning_async


__all__ = [
    "MemoryContext",
    "AsyncMemoryContext",
    "inject_context",
    "track_conversation",
    "learning",
    "learning_async",
    "memory",
    "memory_async",
    "MemoryManager",
    "ContextInjector",
]
