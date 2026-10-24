from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.security import require_viewer
from app.db.session import get_db
from app.db.models import Attendance, Employee

router = APIRouter(prefix="/events", tags=["Jonli Hodisalar"], dependencies=[Depends(require_viewer)])


@router.get("/recent")
def get_recent_events(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Oxirgi o'tishlar lentasi (Jonli monitoring)"""
    rows = (
        db.query(Attendance)
        .order_by(Attendance.event_time.desc())
        .limit(limit)
        .all()
    )

    result = []
    for ev in rows:
        result.append({
            "id": ev.id,
            "emp_no": ev.emp_no,
            "employee_name": ev.employee_name or ev.emp_no,
            "event_type": ev.event_type,
            "event_time": ev.event_time.isoformat() if ev.event_time else None,
            "late_minutes": ev.late_minutes or 0,
            "serial_no": ev.serial_no
        })
    return result
