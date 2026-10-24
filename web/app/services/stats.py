import time
from datetime import date, datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import DailyAttendance, Employee, Attendance

# 30-60 soniya xotirada kesh
_cache: Dict[str, Any] = {}
_cache_expiry: Dict[str, float] = {}


def get_cached(key: str) -> Optional[Any]:
    if key in _cache and time.time() < _cache_expiry.get(key, 0):
        return _cache[key]
    return None


def set_cached(key: str, value: Any, ttl: int = 45):
    _cache[key] = value
    _cache_expiry[key] = time.time() + ttl


def get_overview(db: Session, target_date: Optional[date] = None) -> dict:
    if target_date is None:
        target_date = datetime.now(settings.tz).date()

    cache_key = f"overview_{target_date}"
    cached = get_cached(cache_key)
    if cached is not None:
        return cached

    total_employees = db.query(Employee).filter(Employee.active == True).count()

    records = (
        db.query(DailyAttendance)
        .join(Employee, Employee.emp_no == DailyAttendance.emp_no)
        .filter(DailyAttendance.day == target_date, Employee.active == True)
        .all()
    )

    present_count = 0
    late_count = 0
    absent_count = 0
    on_time_count = 0

    for r in records:
        if r.status in ("present", "late") or r.first_in is not None:
            present_count += 1
            if r.late_minutes > 0:
                late_count += 1
            else:
                on_time_count += 1
        elif r.status == "absent":
            absent_count += 1

    # Agar hali daily_attendance yozilmagan xodimlar bo'lsa
    recorded_emp_nos = {r.emp_no for r in records}
    missing_count = max(0, total_employees - len(recorded_emp_nos))
    absent_count += missing_count

    on_time_percentage = 0.0
    if present_count > 0:
        on_time_percentage = round((on_time_count / present_count) * 100, 1)

    result = {
        "date": str(target_date),
        "total_employees": total_employees,
        "present": present_count,
        "on_time": on_time_count,
        "late": late_count,
        "absent": absent_count,
        "on_time_percentage": on_time_percentage
    }

    set_cached(cache_key, result, ttl=30)
    return result


def get_trend(db: Session, days: int = 30) -> list[dict]:
    cache_key = f"trend_{days}"
    cached = get_cached(cache_key)
    if cached is not None:
        return cached

    today = datetime.now(settings.tz).date()
    start_date = today - timedelta(days=days - 1)

    rows = (
        db.query(
            DailyAttendance.day,
            func.count().label("total"),
            func.sum(func.case((DailyAttendance.late_minutes > 0, 1), else_=0)).label("late_count"),
            func.avg(
                func.case(
                    (DailyAttendance.first_in != None,
                     func.extract("hour", DailyAttendance.first_in) * 60 + func.extract("minute", DailyAttendance.first_in)),
                    else_=None
                )
            ).label("avg_arrival_minutes")
        )
        .join(Employee, Employee.emp_no == DailyAttendance.emp_no)
        .filter(
            DailyAttendance.day >= start_date,
            DailyAttendance.day <= today,
            Employee.active == True
        )
        .group_by(DailyAttendance.day)
        .order_by(DailyAttendance.day.asc())
        .all()
    )

    trend_data = []
    for r in rows:
        total = r.total or 0
        late = r.late_count or 0
        late_pct = round((late / total * 100), 1) if total > 0 else 0.0

        avg_min = r.avg_arrival_minutes
        avg_time_str = None
        if avg_min is not None:
            h = int(avg_min // 60)
            m = int(avg_min % 60)
            avg_time_str = f"{h:02d}:{m:02d}"

        trend_data.append({
            "day": str(r.day),
            "total": total,
            "late_count": late,
            "late_percentage": late_pct,
            "avg_arrival_time": avg_time_str
        })

    set_cached(cache_key, trend_data, ttl=60)
    return trend_data


def get_ranking(db: Session, date_from: date, date_to: date) -> dict:
    cache_key = f"ranking_{date_from}_{date_to}"
    cached = get_cached(cache_key)
    if cached is not None:
        return cached

    # Eng ko'p kechikkan 10 xodim
    most_late_rows = (
        db.query(
            Employee.emp_no,
            Employee.name,
            Employee.department,
            func.count().filter(DailyAttendance.late_minutes > 0).label("late_days"),
            func.sum(DailyAttendance.late_minutes).label("total_late_minutes")
        )
        .join(DailyAttendance, DailyAttendance.emp_no == Employee.emp_no)
        .filter(
            DailyAttendance.day >= date_from,
            DailyAttendance.day <= date_to,
            DailyAttendance.late_minutes > 0
        )
        .group_by(Employee.emp_no, Employee.name, Employee.department)
        .order_by(func.sum(DailyAttendance.late_minutes).desc())
        .limit(10)
        .all()
    )

    most_late = [
        {
            "emp_no": r.emp_no,
            "name": r.name,
            "department": r.department,
            "late_days": r.late_days or 0,
            "total_late_minutes": int(r.total_late_minutes or 0)
        }
        for r in most_late_rows
    ]

    # Eng intizomli 10 xodim
    punctual_rows = (
        db.query(
            Employee.emp_no,
            Employee.name,
            Employee.department,
            func.count().filter(
                (DailyAttendance.first_in != None) & (DailyAttendance.late_minutes == 0)
            ).label("on_time_days"),
            func.count().filter(DailyAttendance.first_in != None).label("present_days")
        )
        .join(DailyAttendance, DailyAttendance.emp_no == Employee.emp_no)
        .filter(
            DailyAttendance.day >= date_from,
            DailyAttendance.day <= date_to,
            Employee.active == True
        )
        .group_by(Employee.emp_no, Employee.name, Employee.department)
        .order_by(
            func.count().filter((DailyAttendance.first_in != None) & (DailyAttendance.late_minutes == 0)).desc(),
            func.count().filter(DailyAttendance.first_in != None).desc()
        )
        .limit(10)
        .all()
    )

    most_punctual = [
        {
            "emp_no": r.emp_no,
            "name": r.name,
            "department": r.department,
            "on_time_days": r.on_time_days or 0,
            "present_days": r.present_days or 0
        }
        for r in punctual_rows
    ]

    result = {
        "most_late": most_late,
        "most_punctual": most_punctual
    }
    set_cached(cache_key, result, ttl=60)
    return result


def get_arrival_histogram(db: Session, date_from: date, date_to: date) -> list[dict]:
    rows = (
        db.query(DailyAttendance.first_in)
        .filter(
            DailyAttendance.day >= date_from,
            DailyAttendance.day <= date_to,
            DailyAttendance.first_in != None
        )
        .all()
    )

    slots = {
        "07:30 gacha": 0,
        "07:30 - 08:00": 0,
        "08:00 - 08:30": 0,
        "08:30 - 09:00": 0,
        "09:00 - 09:30": 0,
        "09:30 - 10:00": 0,
        "10:00 dan keyin": 0
    }

    for (first_in,) in rows:
        if not first_in:
            continue
        t = first_in.time()
        if t < time(7, 30):
            slots["07:30 gacha"] += 1
        elif t < time(8, 0):
            slots["07:30 - 08:00"] += 1
        elif t < time(8, 30):
            slots["08:00 - 08:30"] += 1
        elif t < time(9, 0):
            slots["08:30 - 09:00"] += 1
        elif t < time(9, 30):
            slots["09:00 - 09:30"] += 1
        elif t < time(10, 0):
            slots["09:30 - 10:00"] += 1
        else:
            slots["10:00 dan keyin"] += 1

    return [{"slot": k, "count": v} for k, v in slots.items()]


def get_heatmap(db: Session, date_from: date, date_to: date) -> list[list[int]]:
    """
    Hafta kuni (0: Dushanba .. 6: Yakshanba) x Soat (0 .. 23) o'lchamida kelishlar soni
    Natija: [weekday, hour, count]
    """
    rows = (
        db.query(
            func.extract("dow", DailyAttendance.first_in).label("dow"),
            func.extract("hour", DailyAttendance.first_in).label("hour"),
            func.count().label("count")
        )
        .filter(
            DailyAttendance.day >= date_from,
            DailyAttendance.day <= date_to,
            DailyAttendance.first_in != None
        )
        .group_by("dow", "hour")
        .all()
    )

    # Postgres dow: 0 is Sunday, 1 is Monday ... 6 is Saturday
    # Bizda esa 0: Dushanba .. 6: Yakshanba
    grid = {}
    for r in rows:
        pg_dow = int(r.dow)
        h = int(r.hour)
        count = int(r.count)
        # Convert PG dow (0=Sun..6=Sat) to standard (0=Mon..6=Sun)
        py_dow = (pg_dow + 6) % 7
        grid[(py_dow, h)] = count

    result = []
    for dow in range(7):
        for h in range(24):
            result.append([dow, h, grid.get((dow, h), 0)])
    return result
