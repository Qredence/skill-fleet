#!/usr/bin/env python3
"""
Universal Memory Manager - Local storage for LLM agent memory

Provides persistent memory storage using SQLite or JSON for any LLM agent.
No cloud dependencies required.
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
import hashlib


class MemoryManager:
    """Manager for storing and retrieving agent conversations locally."""

    DEFAULT_MEMORY_PATH = Path.home() / ".droid" / "memory"
    DEFAULT_MEMORY_LIMIT = 10000  # characters

    def __init__(
        self, agent: str, storage_type: str = "sqlite", storage_path: Optional[Path] = None
    ):
        """
        Initialize memory manager for an agent.

        Args:
            agent: Unique agent identifier
            storage_type: "sqlite" or "json"
            storage_path: Custom storage path (defaults to ~/.droid/memory/)
        """
        self.agent = agent
        self.storage_type = storage_type

        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            self.storage_path = self.DEFAULT_MEMORY_PATH / agent

        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        if storage_type == "sqlite":
            self._init_sqlite()
        elif storage_type == "json":
            self._init_json()
        else:
            raise ValueError(f"Unsupported storage type: {storage_type}")

    def _init_sqlite(self):
        """Initialize SQLite database for this agent."""
        self.db_path = self.storage_path.with_suffix(".db")
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                messages TEXT NOT NULL,
                metadata TEXT,
                capture_only INTEGER DEFAULT 0
            )
        """)

        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at 
            ON conversations(created_at DESC)
        """)

        self.conn.commit()

    def _init_json(self):
        """Initialize JSON storage for this agent."""
        self.json_path = self.storage_path.with_suffix(".json")

        if not self.json_path.exists():
            with open(self.json_path, "w") as f:
                json.dump({"conversations": []}, f)

    def save_conversation(
        self,
        messages: List[Dict[str, Any]],
        capture_only: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Save a conversation to storage.

        Args:
            messages: List of message dicts with 'role' and 'content'
            capture_only: If True, don't retrieve this conversation for context
            metadata: Optional metadata (model, tokens, etc.)

        Returns:
            Conversation ID
        """
        timestamp = datetime.utcnow().isoformat() + "Z"

        if self.storage_type == "sqlite":
            cursor = self.conn.execute(
                """
                INSERT INTO conversations (created_at, messages, metadata, capture_only)
                VALUES (?, ?, ?, ?)
                """,
                (timestamp, json.dumps(messages), json.dumps(metadata or {}), int(capture_only)),
            )
            self.conn.commit()
            return cursor.lastrowid

        elif self.storage_type == "json":
            with open(self.json_path, "r") as f:
                data = json.load(f)

            conversation = {
                "id": self._generate_conversation_id(),
                "created_at": timestamp,
                "messages": messages,
                "metadata": metadata or {},
                "capture_only": capture_only,
            }

            data["conversations"].append(conversation)

            with open(self.json_path, "w") as f:
                json.dump(data, f, indent=2)

            return conversation["id"]

    def get_conversations(
        self,
        limit: int = 10,
        include_capture_only: bool = False,
        older_than: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve recent conversations.

        Args:
            limit: Maximum number of conversations to retrieve
            include_capture_only: Include conversations marked as capture_only
            older_than: Only return conversations older than this time

        Returns:
            List of conversation dicts
        """
        if self.storage_type == "sqlite":
            query = "SELECT * FROM conversations WHERE 1=1"
            params = []

            if not include_capture_only:
                query += " AND capture_only = 0"

            if older_than:
                query += " AND created_at < ?"
                params.append(older_than.isoformat() + "Z")

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            cursor = self.conn.execute(query, params)
            rows = cursor.fetchall()

            return [self._row_to_dict(row) for row in rows]

        elif self.storage_type == "json":
            with open(self.json_path, "r") as f:
                data = json.load(f)

            conversations = data["conversations"]

            if not include_capture_only:
                conversations = [c for c in conversations if not c.get("capture_only", False)]

            if older_than:
                conversations = [
                    c
                    for c in conversations
                    if datetime.fromisoformat(c["created_at"].replace("Z", "")) < older_than
                ]

            return sorted(conversations, key=lambda x: x["created_at"], reverse=True)[:limit]

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search conversations by keyword.

        Args:
            query: Search keyword
            limit: Maximum results

        Returns:
            List of matching conversations
        """
        query_lower = query.lower()

        if self.storage_type == "sqlite":
            cursor = self.conn.execute(
                """
                SELECT * FROM conversations 
                WHERE LOWER(messages) LIKE ? 
                ORDER BY created_at DESC 
                LIMIT ?
                """,
                (f"%{query_lower}%", limit),
            )
            rows = cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]

        elif self.storage_type == "json":
            with open(self.json_path, "r") as f:
                data = json.load(f)

            results = []
            for conv in data["conversations"]:
                messages_text = json.dumps(conv["messages"]).lower()
                if query_lower in messages_text:
                    results.append(conv)
                    if len(results) >= limit:
                        break

            return results

    def get_context(self, limit: int = 5, max_tokens: int = 2000) -> str:
        """
        Get formatted context from recent conversations.

        Args:
            limit: Number of recent conversations to include
            max_tokens: Approximate token limit for context

        Returns:
            Formatted context string
        """
        conversations = self.get_conversations(limit=limit, include_capture_only=False)

        if not conversations:
            return ""

        context_parts = []
        total_chars = 0

        for conv in conversations:
            conv_text = self._format_conversation(conv)

            if total_chars + len(conv_text) > max_tokens * 4:  # Approx 4 chars per token
                break

            context_parts.append(conv_text)
            total_chars += len(conv_text)

        return "\n\n".join(context_parts)

    def _format_conversation(self, conv: Dict[str, Any]) -> str:
        """Format a conversation for context injection."""
        messages = conv.get("messages", [])
        formatted = []

        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            formatted.append(f"{role.upper()}: {content}")

        return "\n".join(formatted)

    def _row_to_dict(self, row: tuple) -> Dict[str, Any]:
        """Convert SQLite row to dict."""
        return {
            "id": row[0],
            "created_at": row[1],
            "messages": json.loads(row[2]),
            "metadata": json.loads(row[3]) if row[3] else {},
            "capture_only": bool(row[4]),
        }

    def _generate_conversation_id(self) -> str:
        """Generate unique conversation ID for JSON storage."""
        timestamp = datetime.utcnow().timestamp()
        hash_input = f"{self.agent}{timestamp}".encode()
        return hashlib.md5(hash_input).hexdigest()[:16]

    def clear_conversations(self, older_than_days: Optional[int] = None):
        """
        Clear conversations from storage.

        Args:
            older_than_days: Only clear conversations older than this many days.
                           If None, clear all conversations.
        """
        if older_than_days:
            cutoff = datetime.utcnow().timestamp() - (older_than_days * 86400)
            cutoff_str = datetime.fromtimestamp(cutoff).isoformat() + "Z"
        else:
            cutoff_str = None

        if self.storage_type == "sqlite":
            if cutoff_str:
                self.conn.execute("DELETE FROM conversations WHERE created_at < ?", (cutoff_str,))
            else:
                self.conn.execute("DELETE FROM conversations")
            self.conn.commit()

        elif self.storage_type == "json":
            with open(self.json_path, "r") as f:
                data = json.load(f)

            if cutoff_str:
                data["conversations"] = [
                    c
                    for c in data["conversations"]
                    if datetime.fromisoformat(c["created_at"].replace("Z", ""))
                    >= datetime.fromisoformat(cutoff_str.replace("Z", ""))
                ]
            else:
                data["conversations"] = []

            with open(self.json_path, "w") as f:
                json.dump(data, f, indent=2)

    def export_memory(self, output_path: Path):
        """
        Export all conversations to a JSON file.

        Args:
            output_path: Path to export file
        """
        conversations = self.get_conversations(limit=1000, include_capture_only=True)

        export_data = {
            "agent": self.agent,
            "exported_at": datetime.utcnow().isoformat() + "Z",
            "conversations": conversations,
        }

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(export_data, f, indent=2)

    def import_memory(self, input_path: Path):
        """
        Import conversations from a JSON file.

        Args:
            input_path: Path to import file
        """
        with open(input_path, "r") as f:
            data = json.load(f)

        for conv in data.get("conversations", []):
            self.save_conversation(
                messages=conv["messages"],
                capture_only=conv.get("capture_only", False),
                metadata=conv.get("metadata", {}),
            )

    def close(self):
        """Close database connection (SQLite only)."""
        if hasattr(self, "conn"):
            self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class ContextInjector:
    """Injects context into LLM prompts."""

    @staticmethod
    def inject_context(prompt: str, context: str) -> str:
        """
        Inject context into a prompt.

        Args:
            prompt: Original user prompt
            context: Context from previous conversations

        Returns:
            Enhanced prompt with context
        """
        if not context:
            return prompt

        return f"""Previous Context:
{context}

Current Request:
{prompt}"""

    @staticmethod
    def inject_messages(messages: List[Dict[str, Any]], context: str) -> List[Dict[str, Any]]:
        """
        Inject context as a system message.

        Args:
            messages: Original message list
            context: Context from previous conversations

        Returns:
            Enhanced message list with context
        """
        if not context:
            return messages

        # Insert context as first system message
        enhanced = [
            {
                "role": "system",
                "content": f"Use this context from previous conversations:\n\n{context}",
            }
        ] + messages

        return enhanced
