from datetime import date
from typing import Dict, Any, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.security import require_admin, get_current_user_payload
from app.db.session import get_db
from app.db.models import AppSetting, CalendarDay
from app.services.audit import log_audit

router = APIRouter(prefix="", tags=["Sozlamalar va Taqvim"], dependencies=[Depends(require_admin)])


class CalendarDayRequest(BaseModel):
    day: date
    is_workday: bool
    note: Optional[str] = None


@router.get("/settings")
def get_settings(db: Session = Depends(get_db)):
    rows = db.query(AppSetting).all()
    res = {}
    for r in rows:
        res[r.key] = r.value
    return res


@router.put("/settings/{key}")
def update_setting_key(
    key: str,
    value: Dict[str, Any],
    user_payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    sett = db.query(AppSetting).filter(AppSetting.key == key).first()
    if not sett:
        sett = AppSetting(key=key, value=value)
        db.add(sett)
    else:
        sett.value = value
    db.commit()

    actor_id = int(user_payload.get("sub", 0))
    log_audit(db, actor_id, "SETTING_UPDATE", key, value)
    return {"status": "success", "key": key}


@router.get("/calendar")
def get_calendar_days(
    year: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(CalendarDay)
    if year:
        start_d = date(year, 1, 1)
        end_d = date(year, 12, 31)
        query = query.filter(CalendarDay.day >= start_d, CalendarDay.day <= end_d)
    rows = query.order_by(CalendarDay.day.asc()).all()
    return [
        {"day": str(r.day), "is_workday": r.is_workday, "note": r.note or ""}
        for r in rows
    ]


@router.put("/calendar")
def set_calendar_day(
    data: CalendarDayRequest,
    user_payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    cal = db.query(CalendarDay).filter(CalendarDay.day == data.day).first()
    if not cal:
        cal = CalendarDay(day=data.day, is_workday=data.is_workday, note=data.note)
        db.add(cal)
    else:
        cal.is_workday = data.is_workday
        cal.note = data.note
    db.commit()

    actor_id = int(user_payload.get("sub", 0))
    log_audit(db, actor_id, "CALENDAR_DAY_UPDATE", str(data.day), data.model_dump())
    return {"status": "success", "day": str(data.day)}
