"""Data models and state definitions for DevPilot."""
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class TaskStatus(str, Enum):
    RECEIVED = "RECEIVED"
    UNDERSTANDING = "UNDERSTANDING"
    INVESTIGATING = "INVESTIGATING"
    PLAN_READY = "PLAN_READY"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    IMPLEMENTING = "IMPLEMENTING"
    TESTING = "TESTING"
    PR_CREATED = "PR_CREATED"
    JIRA_UPDATED = "JIRA_UPDATED"
    SLACK_NOTIFIED = "SLACK_NOTIFIED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"


class StepStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TimelineItem(BaseModel):
    id: str
    title: str
    status: StepStatus = StepStatus.PENDING
    details: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class AuditLogEntry(BaseModel):
    id: str
    task_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    action: str
    arguments_summary: Dict[str, Any]
    result: str
    status: str  # "success" or "error"


class ProposedChange(BaseModel):
    file_path: str
    description: str
    diff: Optional[str] = None


class ImplementationPlan(BaseModel):
    summary: str
    steps: List[str] = []
    affected_files: List[str] = []
    tests_to_run: List[str] = []
    branch_name: str = ""


class PullRequestInfo(BaseModel):
    id: int
    number: int
    title: str
    body: str
    html_url: str
    branch: str
    status: str = "open"


class TaskState(BaseModel):
    task_id: str
    user_request: str
    jira_issue: Optional[str] = None
    repository: str = "acme-corp/ai-inference-service"
    branch: Optional[str] = None
    plan: Optional[ImplementationPlan] = None
    affected_files: List[str] = []
    approval_required: bool = True
    approval_status: str = "pending"  # "pending", "approved", "rejected"
    approval_comment: Optional[str] = None
    tests_run: List[str] = []
    test_results: Optional[Dict[str, Any]] = None
    pull_request: Optional[PullRequestInfo] = None
    slack_notification: Optional[Dict[str, Any]] = None
    status: TaskStatus = TaskStatus.RECEIVED
    timeline: List[TimelineItem] = []
    error_message: Optional[str] = None
    root_cause: Optional[str] = None
    diff: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CommandRequest(BaseModel):
    command: str


class ApprovalDecision(BaseModel):
    decision: str  # "approve" or "reject"
    comment: Optional[str] = None


class DailySummary(BaseModel):
    completed: List[Dict[str, Any]] = []
    in_progress: List[Dict[str, Any]] = []
    blocked: List[Dict[str, Any]] = []
    pull_requests: List[Dict[str, Any]] = []
    important_discussions: List[Dict[str, Any]] = []
