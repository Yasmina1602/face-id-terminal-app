from datetime import date, datetime, time
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import require_viewer, require_admin, get_current_user_payload
from app.db.session import get_db
from app.db.models import DailyAttendance, Employee, AttendanceAdjustment
from app.services.aggregator import rebuild
from app.services.audit import log_audit

router = APIRouter(prefix="/attendance", tags=["Davomat"])


class AdjustmentRequest(BaseModel):
    status_override: Optional[str] = None  # present | late | absent | leave | weekend | holiday
    new_first_in: Optional[str] = None    # HH:MM
    reason: Optional[str] = None
    fine_amount: Optional[Decimal] = Decimal(0)


class RebuildRequest(BaseModel):
    day_from: date
    day_to: date


@router.get("", dependencies=[Depends(require_viewer)])
def list_attendance(
    date_from: Optional[date] = Query(None, alias="from"),
    date_to: Optional[date] = Query(None, alias="to"),
    emp_no: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = (
        db.query(
            DailyAttendance,
            Employee.name.label("employee_name"),
            Employee.department.label("department"),
            AttendanceAdjustment.status_override,
            AttendanceAdjustment.reason.label("adj_reason"),
            AttendanceAdjustment.fine_amount.label("adj_fine")
        )
        .join(Employee, Employee.emp_no == DailyAttendance.emp_no)
        .outerjoin(
            AttendanceAdjustment,
            (AttendanceAdjustment.emp_no == DailyAttendance.emp_no) & (AttendanceAdjustment.day == DailyAttendance.day)
        )
    )

    if date_from:
        query = query.filter(DailyAttendance.day >= date_from)
    if date_to:
        query = query.filter(DailyAttendance.day <= date_to)
    if emp_no:
        query = query.filter(DailyAttendance.emp_no == emp_no)
    if status_filter:
        query = query.filter(DailyAttendance.status == status_filter)

    total = query.count()
    rows = (
        query.order_by(
            DailyAttendance.day.desc(),
            func.coalesce(DailyAttendance.last_out, DailyAttendance.first_in).desc().nullslast(),
            Employee.name.asc()
        )
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    items = []
    for daily, emp_name, dept, override, reason, fine in rows:
        items.append({
            "emp_no": daily.emp_no,
            "employee_name": emp_name,
            "department": dept,
            "day": str(daily.day),
            "first_in": daily.first_in.strftime("%H:%M:%S") if daily.first_in else None,
            "last_out": daily.last_out.strftime("%H:%M:%S") if daily.last_out else None,
            "late_minutes": daily.late_minutes,
            "worked_minutes": daily.worked_minutes,
            "events_count": daily.events_count,
            "status": daily.status,
            "has_adjustment": override is not None or reason is not None or fine is not None,
            "adjustment_reason": reason,
            "fine_amount": float(fine) if fine else 0.0
        })

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": items
    }


@router.put("/{emp_no}/{day}/adjustment", dependencies=[Depends(require_admin)])
def update_adjustment(
    emp_no: str,
    day: date,
    data: AdjustmentRequest,
    user_payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    emp = db.query(Employee).filter(Employee.emp_no == emp_no).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Xodim topilmadi")

    adj = (
        db.query(AttendanceAdjustment)
        .filter(AttendanceAdjustment.emp_no == emp_no, AttendanceAdjustment.day == day)
        .first()
    )

    parsed_time = None
    if data.new_first_in:
        parts = data.new_first_in.strip().replace(".", ":").split(":")
        parsed_time = time(int(parts[0]), int(parts[1]) if len(parts) > 1 else 0)

    actor_id = int(user_payload.get("sub", 0))

    if not adj:
        adj = AttendanceAdjustment(
            emp_no=emp_no,
            day=day,
            status_override=data.status_override,
            new_first_in=parsed_time,
            reason=data.reason,
            fine_amount=data.fine_amount or Decimal(0),
            created_by=actor_id
        )
        db.add(adj)
    else:
        adj.status_override = data.status_override
        adj.new_first_in = parsed_time
        adj.reason = data.reason
        adj.fine_amount = data.fine_amount or Decimal(0)
        adj.created_by = actor_id
        adj.created_at = func.now()

    db.commit()

    # Ushbu kunni darhol qayta hisoblash
    rebuild(db, day, day)

    log_audit(db, actor_id, "ATTENDANCE_ADJUSTMENT", f"{emp_no}:{day}", data.model_dump())

    return {"status": "success", "message": "Tuzatish saqlandi va hisob-kitob yangilandi"}


@router.post("/rebuild", dependencies=[Depends(require_admin)])
def trigger_rebuild(
    data: RebuildRequest,
    user_payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    """Admin tomonidan qo'lda aggregatorni ishga tushirish"""
    if (data.day_to - data.day_from).days > 366:
        raise HTTPException(status_code=400, detail="Muddati 366 kundan oshmasligi kerak")

    res = rebuild(db, data.day_from, data.day_to)
    actor_id = int(user_payload.get("sub", 0))
    log_audit(db, actor_id, "AGGREGATOR_REBUILD", f"{data.day_from}_{data.day_to}", res)
    return res
