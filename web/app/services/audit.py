from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.db.models import AuditLog


def log_audit(
    db: Session,
    actor: Optional[int],
    action: str,
    target: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> AuditLog:
    entry = AuditLog(
        actor=actor,
        action=action,
        target=target,
        details=details
    )
    db.add(entry)
    db.commit()
    return entry
