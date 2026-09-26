"""Audit trail system for DevPilot.

Mandatory Spec Requirements (Section 18 & 19):
- Record every important agent action (action name, arguments summary, result, timestamp, status).
- Never store secrets or sensitive credentials in the audit trail.
- Maintain an immutable log for developers and security reviewers.
"""
import uuid
import logging
from typing import Dict, Any, List
from ..models import AuditLogEntry

logger = logging.getLogger("DevPilot.Audit")


class AuditTrail:
    def __init__(self):
        self._entries: List[AuditLogEntry] = []

    def _sanitize(self, data: Any) -> Any:
        sensitive_keys = {"token", "key", "secret", "password", "auth", "bearer"}
        if isinstance(data, dict):
            return {
                k: "[REDACTED]" if any(sk in k.lower() for sk in sensitive_keys) else self._sanitize(v)
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [self._sanitize(item) for item in data]
        return data

    def record(self, task_id: str, action: str, arguments: Dict[str, Any], result: Any, status: str = "success") -> AuditLogEntry:
        sanitized_args = self._sanitize(arguments)
        result_summary = str(result)[:300] if not isinstance(result, str) else result[:300]
        
        entry = AuditLogEntry(
            id=str(uuid.uuid4())[:8],
            task_id=task_id,
            action=action,
            arguments_summary=sanitized_args,
            result=result_summary,
            status=status
        )
        self._entries.append(entry)
        logger.info(f"[Audit] Task={task_id} Action={action} Status={status}")
        return entry

    def get_entries_for_task(self, task_id: str) -> List[AuditLogEntry]:
        return [e for e in self._entries if e.task_id == task_id]

    def get_all_entries(self) -> List[AuditLogEntry]:
        return list(reversed(self._entries))


audit_trail = AuditTrail()
