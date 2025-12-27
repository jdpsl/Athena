"""Job models for task queue."""

from enum import Enum
from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


class JobStatus(str, Enum):
    """Job execution status."""

    PENDING = "pending"
    CLAIMED = "claimed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Job(BaseModel):
    """Represents a job in the queue."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique job ID")
    type: str = Field(description="Job type (e.g., 'code_task', 'explore_codebase')")
    status: JobStatus = Field(default=JobStatus.PENDING, description="Current status")
    priority: int = Field(default=1, description="Job priority (higher = more important)")
    payload: dict[str, Any] = Field(default_factory=dict, description="Job data")
    parent_job_id: Optional[str] = Field(default=None, description="Parent job if this is a sub-job")
    agent_id: Optional[str] = Field(default=None, description="Agent currently handling this job")
    context_id: Optional[str] = Field(default=None, description="Shared context ID")
    result: Optional[dict[str, Any]] = Field(default=None, description="Job result")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    retry_count: int = Field(default=0, description="Number of retries attempted")
    max_retries: int = Field(default=3, description="Maximum retries allowed")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation time")
    claimed_at: Optional[datetime] = Field(default=None, description="When job was claimed")
    started_at: Optional[datetime] = Field(default=None, description="When execution started")
    completed_at: Optional[datetime] = Field(default=None, description="When job completed")

    class Config:
        """Pydantic config."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
