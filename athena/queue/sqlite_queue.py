"""SQLite-based job queue implementation."""

import aiosqlite
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from athena.models.job import Job, JobStatus


class SQLiteJobQueue:
    """SQLite-based job queue for managing tasks."""

    def __init__(self, db_path: str = "athena.db"):
        """Initialize job queue.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.db: Optional[aiosqlite.Connection] = None

    async def initialize(self) -> None:
        """Initialize the database and create tables."""
        self.db = await aiosqlite.connect(self.db_path)
        self.db.row_factory = aiosqlite.Row

        await self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                status TEXT NOT NULL,
                priority INTEGER DEFAULT 1,
                payload TEXT NOT NULL,
                parent_job_id TEXT,
                agent_id TEXT,
                context_id TEXT,
                result TEXT,
                error TEXT,
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                created_at TEXT NOT NULL,
                claimed_at TEXT,
                started_at TEXT,
                completed_at TEXT
            )
            """
        )

        # Create indexes
        await self.db.execute(
            "CREATE INDEX IF NOT EXISTS idx_status ON jobs(status)"
        )
        await self.db.execute(
            "CREATE INDEX IF NOT EXISTS idx_priority ON jobs(priority DESC)"
        )
        await self.db.execute(
            "CREATE INDEX IF NOT EXISTS idx_parent ON jobs(parent_job_id)"
        )

        await self.db.commit()

    async def close(self) -> None:
        """Close the database connection."""
        if self.db:
            await self.db.close()

    async def push(self, job: Job) -> None:
        """Add a job to the queue.

        Args:
            job: Job to add
        """
        if not self.db:
            raise RuntimeError("Database not initialized")

        await self.db.execute(
            """
            INSERT INTO jobs (
                id, type, status, priority, payload, parent_job_id,
                agent_id, context_id, result, error, retry_count,
                max_retries, created_at, claimed_at, started_at, completed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job.id,
                job.type,
                job.status.value,
                job.priority,
                json.dumps(job.payload),
                job.parent_job_id,
                job.agent_id,
                job.context_id,
                json.dumps(job.result) if job.result else None,
                job.error,
                job.retry_count,
                job.max_retries,
                job.created_at.isoformat(),
                job.claimed_at.isoformat() if job.claimed_at else None,
                job.started_at.isoformat() if job.started_at else None,
                job.completed_at.isoformat() if job.completed_at else None,
            ),
        )
        await self.db.commit()

    async def claim(self, agent_id: str) -> Optional[Job]:
        """Claim the next pending job.

        Args:
            agent_id: ID of the agent claiming the job

        Returns:
            Claimed job or None if no jobs available
        """
        if not self.db:
            raise RuntimeError("Database not initialized")

        async with self.db.execute(
            """
            SELECT * FROM jobs
            WHERE status = ?
            ORDER BY priority DESC, created_at ASC
            LIMIT 1
            """,
            (JobStatus.PENDING.value,),
        ) as cursor:
            row = await cursor.fetchone()

        if not row:
            return None

        # Claim the job
        claimed_at = datetime.utcnow()
        await self.db.execute(
            """
            UPDATE jobs
            SET status = ?, agent_id = ?, claimed_at = ?
            WHERE id = ?
            """,
            (JobStatus.CLAIMED.value, agent_id, claimed_at.isoformat(), row["id"]),
        )
        await self.db.commit()

        return self._row_to_job(row)

    async def update_status(
        self,
        job_id: str,
        status: JobStatus,
        result: Optional[dict] = None,
        error: Optional[str] = None,
    ) -> None:
        """Update job status.

        Args:
            job_id: Job ID
            status: New status
            result: Job result (optional)
            error: Error message (optional)
        """
        if not self.db:
            raise RuntimeError("Database not initialized")

        now = datetime.utcnow().isoformat()

        updates = ["status = ?"]
        params: list = [status.value]

        if status == JobStatus.IN_PROGRESS:
            updates.append("started_at = ?")
            params.append(now)

        if status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
            updates.append("completed_at = ?")
            params.append(now)

        if result is not None:
            updates.append("result = ?")
            params.append(json.dumps(result))

        if error is not None:
            updates.append("error = ?")
            params.append(error)

        params.append(job_id)

        await self.db.execute(
            f"UPDATE jobs SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        await self.db.commit()

    async def get(self, job_id: str) -> Optional[Job]:
        """Get a job by ID.

        Args:
            job_id: Job ID

        Returns:
            Job or None if not found
        """
        if not self.db:
            raise RuntimeError("Database not initialized")

        async with self.db.execute(
            "SELECT * FROM jobs WHERE id = ?", (job_id,)
        ) as cursor:
            row = await cursor.fetchone()

        return self._row_to_job(row) if row else None

    async def get_children(self, parent_job_id: str) -> list[Job]:
        """Get all child jobs of a parent.

        Args:
            parent_job_id: Parent job ID

        Returns:
            List of child jobs
        """
        if not self.db:
            raise RuntimeError("Database not initialized")

        async with self.db.execute(
            "SELECT * FROM jobs WHERE parent_job_id = ?", (parent_job_id,)
        ) as cursor:
            rows = await cursor.fetchall()

        return [self._row_to_job(row) for row in rows]

    def _row_to_job(self, row: aiosqlite.Row) -> Job:
        """Convert database row to Job object.

        Args:
            row: Database row

        Returns:
            Job object
        """
        return Job(
            id=row["id"],
            type=row["type"],
            status=JobStatus(row["status"]),
            priority=row["priority"],
            payload=json.loads(row["payload"]),
            parent_job_id=row["parent_job_id"],
            agent_id=row["agent_id"],
            context_id=row["context_id"],
            result=json.loads(row["result"]) if row["result"] else None,
            error=row["error"],
            retry_count=row["retry_count"],
            max_retries=row["max_retries"],
            created_at=datetime.fromisoformat(row["created_at"]),
            claimed_at=(
                datetime.fromisoformat(row["claimed_at"]) if row["claimed_at"] else None
            ),
            started_at=(
                datetime.fromisoformat(row["started_at"]) if row["started_at"] else None
            ),
            completed_at=(
                datetime.fromisoformat(row["completed_at"])
                if row["completed_at"]
                else None
            ),
        )
