"""FastAPI server for skill creation with real-time streaming.

This module provides a REST API for skill creation with Server-Sent Events (SSE)
streaming support for real-time thinking/reasoning display.

Based on: https://dspy.ai/tutorials/deployment/#deploying-with-fastapi

Usage:
    # Start the server
    uv run uvicorn skill_fleet.api.app:app --reload --port 8000

    # Test the streaming endpoint
    curl -N http://127.0.0.1:8000/api/v1/create-skill/stream \\
        -H "Content-Type: application/json" \\
        -d '{"task_description": "Create an OpenAPI skill"}'
"""

from __future__ import annotations

import logging
from typing import Any

import dspy
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..common.paths import default_config_path
from ..common.streaming import (
    create_async_module,
    create_streaming_module,
    stream_dspy_response,
)
from ..llm.fleet_config import build_lm_for_task, load_fleet_config

logger = logging.getLogger(__name__)

# Default config path
DEFAULT_CONFIG_PATH = default_config_path()

# Configure async workers for FastAPI
dspy.configure(async_max_workers=4)


# ============================================================================
# LLM Configuration
# ============================================================================


def _configure_llm() -> dict[str, dspy.LM]:
    """Configure LLM for the API.

    Loads the fleet configuration and builds LLM instances for required tasks.
    Returns a dictionary of task_name -> LM mappings.

    Returns:
        Dictionary mapping task names to dspy.LM instances
    """
    try:
        config = load_fleet_config(DEFAULT_CONFIG_PATH)
        task_names = ["skill_understand", "skill_validate", "skill_create"]
        task_lms = {task_name: build_lm_for_task(config, task_name) for task_name in task_names}
        # Set default LM
        if task_lms:
            dspy.configure(lm=list(task_lms.values())[0])
        return task_lms
    except Exception as e:
        logger.warning(f"Failed to load fleet config: {e}. Using defaults.")
        # Return empty dict - agent will use dspy.settings.lm
        return {}


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Skill Fleet API",
    description="AI-powered skill creation with real-time streaming",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# ============================================================================
# Request/Response Models
# ============================================================================


class TaskRequest(BaseModel):
    """Request model for skill creation."""

    task_description: str = Field(
        ...,
        description="The task description for skill creation",
        min_length=10,
        examples=["Create an OpenAPI skill for validating API endpoints"],
    )
    stream: bool = Field(
        default=True,
        description="Enable streaming for real-time thinking display",
    )


class TaskResponse(BaseModel):
    """Response model for non-streaming skill creation."""

    status: str = Field(description="Status of the request")
    data: dict[str, Any] | None = Field(default=None, description="Result data")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    async_workers: int


# ============================================================================
# API Endpoints
# ============================================================================


@app.get("/", response_model=dict[str, str])
async def root() -> dict[str, str]:
    """Root endpoint with API information."""
    return {
        "message": "Skill Fleet API - AI-powered skill creation",
        "docs": "/docs",
        "health": "/health",
        "streaming": "/api/v1/create-skill/stream",
    }


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        async_workers=dspy.settings.async_max_workers,
    )


@app.post("/api/v1/create-skill", response_model=TaskResponse)
async def create_skill(request: TaskRequest) -> TaskResponse:
    """Create a skill (non-streaming, returns full result when complete).

    This endpoint waits for the entire skill creation process to complete
    before returning the result. Use the /stream endpoint for real-time updates.

    Args:
        request: Task request with description

    Returns:
        TaskResponse with status and data

    Raises:
        HTTPException: If skill creation fails
    """
    try:
        # Import here to avoid circular imports
        from ..agent.agent import ConversationalSkillAgent

        # Configure LLM
        _configure_llm()

        # Create agent
        agent = ConversationalSkillAgent()

        # Wrap with async for FastAPI
        async_agent = create_async_module(agent)

        # Execute skill creation
        result = await async_agent(task_description=request.task_description)

        return TaskResponse(status="success", data=result.toDict())

    except Exception as e:
        logger.error(f"Skill creation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Skill creation failed: {str(e)}",
        ) from e


@app.post("/api/v1/create-skill/stream")
async def create_skill_stream(request: TaskRequest) -> StreamingResponse:
    """Create a skill with real-time streaming (Server-Sent Events).

    This endpoint streams:
    - Reasoning tokens from the LLM (thinking process)
    - Status messages (LM calls, tool calls, module execution)
    - Final prediction result

    The stream uses Server-Sent Events (SSE) format:
        data: {"type": "reasoning", "chunk": "..."}
        data: {"type": "status", "message": "..."}
        data: {"type": "prediction", "data": {...}}
        data: [DONE]

    Args:
        request: Task request with description

    Returns:
        StreamingResponse with SSE media type

    Example:
        ```python
        import requests
        import json

        response = requests.post(
            "http://127.0.0.1:8000/api/v1/create-skill/stream",
            json={"task_description": "Create an OpenAPI skill"},
            stream=True
        )

        for line in response.iter_lines():
            if line:
                data = json.loads(line.decode().replace("data: ", ""))
                if data == "[DONE]":
                    break
                print(data)
        ```
    """
    try:
        # Import here to avoid circular imports
        from ..agent.agent import ConversationalSkillAgent

        # Configure LLM
        _configure_llm()

        # Create agent
        agent = ConversationalSkillAgent()

        # Wrap with async + streaming
        async_agent = create_async_module(agent)
        streaming_agent = create_streaming_module(
            async_agent,
            reasoning_field="reasoning",
            async_mode=True,
        )

        # Create SSE stream generator
        async def generate() -> Any:
            async for chunk in stream_dspy_response(
                streaming_agent, task_description=request.task_description
            ):
                yield chunk

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
            },
        )

    except Exception as e:
        logger.error(f"Streaming skill creation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Streaming failed: {str(e)}",
        ) from e


# ============================================================================
# Startup/Shutdown Events
# ============================================================================


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize resources on startup."""
    logger.info("Starting Skill Fleet API...")
    _configure_llm()
    logger.info("Skill Fleet API ready")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Clean up resources on shutdown."""
    logger.info("Shutting down Skill Fleet API...")


# ============================================================================
# Development Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "skill_fleet.api.app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info",
    )
