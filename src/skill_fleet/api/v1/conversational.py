"""
Conversational interface routes for v1 API.

This module provides endpoints for chat and conversational interactions.

Note: These endpoints are temporarily unavailable pending migration to new workflow architecture.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from skill_fleet.infrastructure.db.database import get_db

from ..schemas.conversational import (
    SendMessageRequest,
    SendMessageResponse,
    SessionHistoryResponse,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session as DbSession


logger = logging.getLogger(__name__)

router = APIRouter()

# Type alias for database dependency
DbSessionDep = Annotated["DbSession", Depends(get_db)]


@router.post("/message", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
    db: DbSessionDep,
) -> SendMessageResponse:
    """
    Send a message in a conversation.

    Temporarily unavailable - pending migration to new workflow architecture.
    """
    raise HTTPException(
        status_code=503,
        detail="Conversational interface is temporarily unavailable. Migration to new workflow architecture in progress.",
    )


@router.post("/session/{session_id}", response_model=dict[str, str])
async def create_session(
    session_id: str,
    db: DbSessionDep,
) -> dict[str, str]:
    """
    Create or resume a conversation session.

    Temporarily unavailable - pending migration to new workflow architecture.
    """
    raise HTTPException(
        status_code=503,
        detail="Conversational interface is temporarily unavailable. Migration to new workflow architecture in progress.",
    )


@router.get("/session/{session_id}/history", response_model=SessionHistoryResponse)
async def get_session_history(
    session_id: str,
    db: DbSessionDep,
) -> SessionHistoryResponse:
    """
    Get the history of a conversation session.

    Temporarily unavailable - pending migration to new workflow architecture.
    """
    raise HTTPException(
        status_code=503,
        detail="Conversational interface is temporarily unavailable. Migration to new workflow architecture in progress.",
    )


@router.get("/sessions", response_model=dict[str, Any])
async def list_sessions(
    db: DbSessionDep,
) -> dict[str, Any]:
    """
    List all active conversation sessions.

    Temporarily unavailable - pending migration to new workflow architecture.
    """
    raise HTTPException(
        status_code=503,
        detail="Conversational interface is temporarily unavailable. Migration to new workflow architecture in progress.",
    )


@router.post("/stream")
async def stream_chat(
    request: SendMessageRequest,
    db: DbSessionDep,
):
    """
    Stream chat responses.

    Temporarily unavailable - pending migration to new workflow architecture.
    """
    raise HTTPException(
        status_code=503,
        detail="Conversational interface is temporarily unavailable. Migration to new workflow architecture in progress.",
    )
