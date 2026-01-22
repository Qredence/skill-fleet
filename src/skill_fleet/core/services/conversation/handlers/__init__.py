"""Conversation handler exports."""

from .exploration import ExplorationHandlers
from .tdd import TDDHandlers


class ConversationHandlers(ExplorationHandlers, TDDHandlers):
    """
    Combined conversation handlers.

    Inherits from phase-specific handlers to provide a unified interface
    for the ConversationService.
    """

    pass


__all__ = ["ExplorationHandlers", "TDDHandlers", "ConversationHandlers"]
