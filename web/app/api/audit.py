from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import require_admin
from app.db.session import get_db
from app.db.models import AuditLog

router = APIRouter(prefix="/audit", tags=["Audit Jurnali"], dependencies=[Depends(require_admin)])


@router.get("")
def list_audit_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    total = db.query(AuditLog).count()
    items = (
        db.query(AuditLog)
        .order_by(AuditLog.at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": [
            {
                "id": a.id,
                "at": a.at.isoformat() if a.at else None,
                "actor": a.actor,
                "action": a.action,
                "target": a.target,
                "details": a.details
            }
            for a in items
        ]
    }
