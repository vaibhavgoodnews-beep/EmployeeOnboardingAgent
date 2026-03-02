from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Callable


def log_action(
    db_write: Callable[..., int],
    agent_name: str,
    action: str,
    employee_id: int | None = None,
    project_id: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> int:
    payload = json.dumps(metadata or {}, ensure_ascii=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    return db_write(
        query="""
        INSERT INTO AuditLogs (agent_name, action, timestamp, employee_id, project_id, metadata)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        params=(agent_name, action, timestamp, employee_id, project_id, payload),
    )
