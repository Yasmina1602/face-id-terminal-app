import logging
from datetime import date, datetime, time, timedelta
from typing import Optional, Set
from zoneinfo import ZoneInfo
from sqlalchemy import func, and_, select
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from app.core.config import settings
from app.db.models import (
    Employee, Attendance, DailyAttendance, AttendanceAdjustment,
    CalendarDay, AppSetting
)

logger = logging.getLogger("aggregator")


def get_general_settings(db: Session) -> dict:
    sett = db.query(AppSetting).filter(AppSetting.key == "general").first()
    if sett and isinstance(sett.value, dict):
        return sett.value
    return {
        "work_start": "09:00",
        "grace_minutes": 0,
        "retention_days": 180,
        "weekend_days": [6]  # 6 = Yakshanba
    }


def calc_late(t: datetime, start_time: time, grace_minutes: int) -> int:
    base = datetime.combine(t.date(), start_time)
    if t <= base + timedelta(minutes=grace_minutes):
        return 0
    return max(1, int((t - base).total_seconds() // 60))


def rebuild(db: Session, day_from: date, day_to: date) -> dict:
    """
    Idempotent aggregation function for daily_attendance table.
    Section 6.3:
    first_in = shu kundagi birinchi checkIn, last_out = oxirgi checkOut,
    late_minutes = shu birinchi kirishdagi qiymat, worked_minutes = last_out - first_in.
    Status: late (late>0), present, aks holda ish kuni bo'lsa va kun tugagan bo'lsa absent; dam olish/bayram bo'lsa weekend/holiday.
    attendance_adjustments bor bo'lsa status_override va new_first_in bosadi.
    """
    gen_sett = get_general_settings(db)
    grace_minutes = int(gen_sett.get("grace_minutes", 0))
    weekend_days: Set[int] = set(gen_sett.get("weekend_days", [6]))

    tz = settings.tz
    now = datetime.now(tz).replace(tzinfo=None)
    today = now.date()

    # Xodimlarni olish (faol va nofaol, agar o'sha paytda yozuv bo'lgan bo'lsa)
    employees = db.query(Employee).all()
    emp_map = {e.emp_no: e for e in employees}

    total_records = 0
    cur_day = day_from

    while cur_day <= day_to:
        day_start = datetime.combine(cur_day, time.min)
        day_end = datetime.combine(cur_day, time.max)

        # 1. Taqvim kunini tekshirish
        cal_day = db.query(CalendarDay).filter(CalendarDay.day == cur_day).first()
        is_workday = True
        is_holiday = False
        is_weekend = False

        if cal_day:
            is_workday = cal_day.is_workday
            if not is_workday:
                is_holiday = True
        else:
            if cur_day.weekday() in weekend_days:
                is_workday = False
                is_weekend = True

        # 2. Ushbu kundagi xom attendance yozuvlarini olish
        raw_events = (
            db.query(Attendance)
            .filter(Attendance.event_time >= day_start, Attendance.event_time <= day_end)
            .order_by(Attendance.event_time.asc())
            .all()
        )

        events_by_emp: dict[str, list[Attendance]] = {}
        for ev in raw_events:
            if not ev.emp_no:
                continue
            events_by_emp.setdefault(ev.emp_no, []).append(ev)

        # 3. Ushbu kundagi qo'lda tuzatishlarni olish
        adjustments = (
            db.query(AttendanceAdjustment)
            .filter(AttendanceAdjustment.day == cur_day)
            .all()
        )
        adj_map = {adj.emp_no: adj for adj in adjustments}

        # 4. Har bir xodim uchun kunlik holatni yig'ish
        for emp_no, emp in emp_map.items():
            emp_events = events_by_emp.get(emp_no, [])
            adj = adj_map.get(emp_no)

            # Agar xodim nofaol bo'lsa va bu kuni hech qanday event bo'lmasa, o'tkazib yuboramiz
            if not emp.active and not emp_events and not adj:
                continue

            first_in_dt = None
            last_out_dt = None
            late_min = 0
            worked_min = None
            events_count = len(emp_events)

            # Birinchi checkIn va oxirgi checkOut
            checkins = [ev for ev in emp_events if ev.event_type == "checkIn"]
            checkouts = [ev for ev in emp_events if ev.event_type == "checkOut"]

            if checkins:
                first_in_ev = checkins[0]
                first_in_dt = first_in_ev.event_time
                late_min = calc_late(first_in_dt, emp.work_start, grace_minutes)

            if checkouts:
                last_out_dt = checkouts[-1].event_time

            if first_in_dt and last_out_dt and last_out_dt > first_in_dt:
                worked_min = int((last_out_dt - first_in_dt).total_seconds() // 60)

            # Boshlang'ich status
            if first_in_dt:
                status = "late" if late_min > 0 else "present"
            else:
                if not is_workday:
                    status = "holiday" if is_holiday else "weekend"
                else:
                    if cur_day < today:
                        status = "absent"
                    else:
                        # Bugungi kun hali tugamagan bo'lsa
                        status = "absent" if now.time() > emp.work_start else "present"

            # Agar qo'lda tuzatish kiritilgan bo'lsa, ustiga yozamiz
            if adj:
                if adj.status_override:
                    status = adj.status_override
                if adj.new_first_in:
                    first_in_dt = datetime.combine(cur_day, adj.new_first_in)
                    late_min = calc_late(first_in_dt, emp.work_start, grace_minutes)
                    if status in ("present", "late"):
                        status = "late" if late_min > 0 else "present"

            # Upsert into daily_attendance
            stmt = insert(DailyAttendance).values(
                emp_no=emp_no,
                day=cur_day,
                first_in=first_in_dt,
                last_out=last_out_dt,
                late_minutes=late_min,
                worked_minutes=worked_min,
                events_count=events_count,
                status=status
            ).on_conflict_do_update(
                index_elements=["emp_no", "day"],
                set_=dict(
                    first_in=first_in_dt,
                    last_out=last_out_dt,
                    late_minutes=late_min,
                    worked_minutes=worked_min,
                    events_count=events_count,
                    status=status
                )
            )
            db.execute(stmt)
            total_records += 1

        cur_day += timedelta(days=1)

    db.commit()
    logger.info("Aggregator rebuild tugadi: %s - %s (%s yozuv)", day_from, day_to, total_records)
    return {
        "status": "success",
        "day_from": str(day_from),
        "day_to": str(day_to),
        "total_records": total_records
    }
