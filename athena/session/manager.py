"""Database-based session manager for conversation persistence."""

import aiosqlite
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
from athena.models.message import Message, Role, ToolCall


class SessionManager:
    """Manages conversation sessions with persistence to athena.db."""

    def __init__(self, db_path: str = "athena.db"):
        """Initialize session manager.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.db: Optional[aiosqlite.Connection] = None
        self.current_session_id: Optional[str] = None

    async def initialize(self) -> None:
        """Initialize the database and create tables."""
        self.db = await aiosqlite.connect(self.db_path)
        self.db.row_factory = aiosqlite.Row

        # Create sessions table
        await self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                working_directory TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_active TEXT NOT NULL,
                message_count INTEGER DEFAULT 0,
                metadata TEXT
            )
            """
        )

        # Create messages table
        await self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS session_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT,
                tool_call_id TEXT,
                name TEXT,
                thinking TEXT,
                tool_calls TEXT,
                sequence INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
            """
        )

        # Create indexes
        await self.db.execute(
            "CREATE INDEX IF NOT EXISTS idx_session_messages ON session_messages(session_id, sequence)"
        )
        await self.db.execute(
            "CREATE INDEX IF NOT EXISTS idx_session_last_active ON sessions(last_active DESC)"
        )

        await self.db.commit()

    async def close(self) -> None:
        """Close the database connection."""
        if self.db:
            await self.db.close()

    async def has_previous_session(self, working_directory: str) -> bool:
        """Check if there's a previous session for this working directory.

        Args:
            working_directory: Working directory path

        Returns:
            True if previous session exists
        """
        if not self.db:
            raise RuntimeError("Database not initialized")

        cursor = await self.db.execute(
            """
            SELECT COUNT(*) FROM sessions
            WHERE working_directory = ?
            """,
            (working_directory,)
        )

        row = await cursor.fetchone()
        return row[0] > 0

    async def get_latest_session(self, working_directory: str) -> Optional[dict]:
        """Get the most recent session for a working directory.

        Args:
            working_directory: Working directory path

        Returns:
            Session dict or None if no previous session
        """
        if not self.db:
            raise RuntimeError("Database not initialized")

        cursor = await self.db.execute(
            """
            SELECT id, working_directory, created_at, last_active, message_count, metadata
            FROM sessions
            WHERE working_directory = ?
            ORDER BY last_active DESC
            LIMIT 1
            """,
            (working_directory,)
        )

        row = await cursor.fetchone()
        if row:
            return {
                "id": row[0],
                "working_directory": row[1],
                "created_at": datetime.fromisoformat(row[2]),
                "last_active": datetime.fromisoformat(row[3]),
                "message_count": row[4],
                "metadata": json.loads(row[5]) if row[5] else {}
            }
        return None

    async def create_session(self, working_directory: str, metadata: Optional[dict] = None) -> str:
        """Create a new session.

        Args:
            working_directory: Working directory path
            metadata: Optional session metadata

        Returns:
            Session ID
        """
        if not self.db:
            raise RuntimeError("Database not initialized")

        session_id = str(uuid.uuid4())
        now = datetime.now()

        await self.db.execute(
            """
            INSERT INTO sessions (id, working_directory, created_at, last_active, message_count, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                working_directory,
                now.isoformat(),
                now.isoformat(),
                0,
                json.dumps(metadata) if metadata else None
            )
        )

        await self.db.commit()
        self.current_session_id = session_id
        return session_id

    async def resume_session(self, session_id: str) -> None:
        """Resume an existing session.

        Args:
            session_id: Session ID to resume
        """
        if not self.db:
            raise RuntimeError("Database not initialized")

        # Update last_active timestamp
        await self.db.execute(
            """
            UPDATE sessions
            SET last_active = ?
            WHERE id = ?
            """,
            (datetime.now().isoformat(), session_id)
        )

        await self.db.commit()
        self.current_session_id = session_id

    async def save_message(self, message: Message, sequence: int) -> None:
        """Save a message to the current session.

        Args:
            message: Message to save
            sequence: Message sequence number
        """
        if not self.db or not self.current_session_id:
            raise RuntimeError("No active session")

        # Serialize tool calls if present
        tool_calls_json = None
        if message.tool_calls:
            tool_calls_json = json.dumps([
                {
                    "id": tc.id,
                    "name": tc.name,
                    "parameters": tc.parameters
                }
                for tc in message.tool_calls
            ])

        await self.db.execute(
            """
            INSERT INTO session_messages (
                session_id, role, content, tool_call_id, name, thinking,
                tool_calls, sequence, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                self.current_session_id,
                message.role.value,
                message.content,
                message.tool_call_id,
                message.name,
                message.thinking,
                tool_calls_json,
                sequence,
                datetime.now().isoformat()
            )
        )

        # Update session message count and last_active
        await self.db.execute(
            """
            UPDATE sessions
            SET message_count = message_count + 1,
                last_active = ?
            WHERE id = ?
            """,
            (datetime.now().isoformat(), self.current_session_id)
        )

        await self.db.commit()

    async def load_messages(self, session_id: str) -> list[Message]:
        """Load all messages from a session.

        Args:
            session_id: Session ID to load messages from

        Returns:
            List of messages in sequence order
        """
        if not self.db:
            raise RuntimeError("Database not initialized")

        cursor = await self.db.execute(
            """
            SELECT role, content, tool_call_id, name, thinking, tool_calls
            FROM session_messages
            WHERE session_id = ?
            ORDER BY sequence ASC
            """,
            (session_id,)
        )

        messages = []
        async for row in cursor:
            # Deserialize tool calls if present
            tool_calls = None
            if row[5]:  # tool_calls column
                tool_calls_data = json.loads(row[5])
                tool_calls = [
                    ToolCall(
                        id=tc["id"],
                        name=tc["name"],
                        parameters=tc["parameters"]
                    )
                    for tc in tool_calls_data
                ]

            message = Message(
                role=Role(row[0]),
                content=row[1],
                tool_call_id=row[2],
                name=row[3],
                thinking=row[4],
                tool_calls=tool_calls
            )
            messages.append(message)

        return messages

    async def delete_session(self, session_id: str) -> None:
        """Delete a session and all its messages.

        Args:
            session_id: Session ID to delete
        """
        if not self.db:
            raise RuntimeError("Database not initialized")

        # Delete messages first
        await self.db.execute(
            "DELETE FROM session_messages WHERE session_id = ?",
            (session_id,)
        )

        # Delete session
        await self.db.execute(
            "DELETE FROM sessions WHERE id = ?",
            (session_id,)
        )

        await self.db.commit()

        if self.current_session_id == session_id:
            self.current_session_id = None
