import calendar
from datetime import time, date, datetime
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.security import require_viewer, require_admin, get_current_user_payload
from app.db.session import get_db
from app.db.models import Employee, ConfigVersion, DailyAttendance, AttendanceAdjustment, Attendance
from app.services.audit import log_audit

router = APIRouter(prefix="/employees", tags=["Xodimlar"])


class EmployeeCreate(BaseModel):
    emp_no: str
    name: str
    work_start: str = "09:00"
    department: Optional[str] = None
    job_title: Optional[str] = None
    active: bool = True


class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    work_start: Optional[str] = None
    department: Optional[str] = None
    job_title: Optional[str] = None
    active: Optional[bool] = None


def parse_time_str(t_str: str) -> time:
    parts = t_str.strip().replace(".", ":").split(":")
    return time(int(parts[0]), int(parts[1]) if len(parts) > 1 else 0)


def bump_version(db: Session):
    ver = db.query(ConfigVersion).filter(ConfigVersion.id == 1).first()
    if ver:
        ver.version += 1
    else:
        db.add(ConfigVersion(id=1, version=2))
    db.commit()


@router.get("", dependencies=[Depends(require_viewer)])
def list_employees(
    search: Optional[str] = None,
    department: Optional[str] = None,
    active: Optional[bool] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(Employee)
    if search:
        s = f"%{search}%"
        query = query.filter(or_(Employee.name.ilike(s), Employee.emp_no.ilike(s)))
    if department:
        query = query.filter(Employee.department == department)
    if active is not None:
        query = query.filter(Employee.active == active)

    total = query.count()
    items = (
        query.order_by(Employee.name.asc())
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
                "emp_no": e.emp_no,
                "name": e.name,
                "work_start": f"{e.work_start:%H:%M}",
                "active": e.active,
                "department": e.department,
                "job_title": e.job_title,
                "updated_at": e.updated_at.isoformat() if e.updated_at else None
            }
            for e in items
        ]
    }


@router.post("", dependencies=[Depends(require_admin)])
def create_employee(
    data: EmployeeCreate,
    user_payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    existing = db.query(Employee).filter(Employee.emp_no == data.emp_no).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'{data.emp_no}' raqamli xodim allaqachon mavjud"
        )

    w_start = parse_time_str(data.work_start)
    emp = Employee(
        emp_no=data.emp_no,
        name=data.name,
        work_start=w_start,
        department=data.department,
        job_title=data.job_title,
        active=data.active
    )
    db.add(emp)
    db.commit()

    bump_version(db)
    actor_id = int(user_payload.get("sub", 0))
    log_audit(db, actor_id, "EMPLOYEE_CREATE", data.emp_no, data.model_dump())

    return {"status": "success", "emp_no": emp.emp_no}


@router.get("/{emp_no}", dependencies=[Depends(require_viewer)])
def get_employee(emp_no: str, db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.emp_no == emp_no).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Xodim topilmadi")

    return {
        "emp_no": emp.emp_no,
        "name": emp.name,
        "work_start": f"{emp.work_start:%H:%M}",
        "active": emp.active,
        "department": emp.department,
        "job_title": emp.job_title,
        "updated_at": emp.updated_at.isoformat() if emp.updated_at else None
    }


@router.patch("/{emp_no}", dependencies=[Depends(require_admin)])
def update_employee(
    emp_no: str,
    data: EmployeeUpdate,
    user_payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    emp = db.query(Employee).filter(Employee.emp_no == emp_no).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Xodim topilmadi")

    if data.name is not None:
        emp.name = data.name
    if data.work_start is not None:
        emp.work_start = parse_time_str(data.work_start)
    if data.department is not None:
        emp.department = data.department
    if data.job_title is not None:
        emp.job_title = data.job_title
    if data.active is not None:
        emp.active = data.active

    emp.updated_at = func.now()
    db.commit()

    bump_version(db)
    actor_id = int(user_payload.get("sub", 0))
    log_audit(db, actor_id, "EMPLOYEE_UPDATE", emp_no, data.model_dump(exclude_unset=True))

    return {"status": "success", "message": "Xodim ma'lumotlari yangilandi"}


@router.get("/{emp_no}/calendar", dependencies=[Depends(require_viewer)])
def get_employee_calendar(
    emp_no: str,
    month: str = Query(..., description="Format: YYYY-MM"),
    db: Session = Depends(get_db)
):
    """Xodimning oylik kalendar davomati"""
    emp = db.query(Employee).filter(Employee.emp_no == emp_no).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Xodim topilmadi")

    try:
        year_str, month_str = month.split("-")
        year = int(year_str)
        month_int = int(month_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Noto'g'ri oy formati. Masalan: 2026-10")

    num_days = calendar.monthrange(year, month_int)[1]
    start_date = date(year, month_int, 1)
    end_date = date(year, month_int, num_days)

    records = (
        db.query(DailyAttendance)
        .filter(
            DailyAttendance.emp_no == emp_no,
            DailyAttendance.day >= start_date,
            DailyAttendance.day <= end_date
        )
        .all()
    )
    record_map = {r.day: r for r in records}

    days_result = []
    for d in range(1, num_days + 1):
        cur_d = date(year, month_int, d)
        rec = record_map.get(cur_d)
        days_result.append({
            "day": str(cur_d),
            "weekday": cur_d.weekday(),
            "first_in": rec.first_in.strftime("%H:%M") if (rec and rec.first_in) else None,
            "last_out": rec.last_out.strftime("%H:%M") if (rec and rec.last_out) else None,
            "late_minutes": rec.late_minutes if rec else 0,
            "worked_minutes": rec.worked_minutes if rec else None,
            "status": rec.status if rec else "absent"
        })

    return {
        "emp_no": emp.emp_no,
        "name": emp.name,
        "month": month,
        "days": days_result
    }
