import logging
from datetime import datetime, date, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import settings
from app.db.session import SessionLocal
from app.db.models import DailyAttendance, Attendance
from app.services.aggregator import rebuild

logger = logging.getLogger("scheduler")
scheduler = BackgroundScheduler(timezone=settings.tz)


def job_rebuild_today():
    """Bugungi kunni har 5 daqiqada yangilash"""
    db = SessionLocal()
    try:
        today = datetime.now(settings.tz).date()
        logger.debug("Scheduler: Bugungi kunni qayta yig'ish boshlandi: %s", today)
        rebuild(db, today, today)
    except Exception as e:
        logger.error("job_rebuild_today xatosi: %s", e)
    finally:
        db.close()


def job_rebuild_recent():
    """Har kecha 00:30 da oxirgi 7 kunni to'liq qayta hisoblash"""
    db = SessionLocal()
    try:
        today = datetime.now(settings.tz).date()
        date_from = today - timedelta(days=7)
        logger.info("Scheduler: Oxirgi 7 kunni qayta yig'ish: %s - %s", date_from, today)
        rebuild(db, date_from, today)
    except Exception as e:
        logger.error("job_rebuild_recent xatosi: %s", e)
    finally:
        db.close()


def initial_sync_if_needed():
    """Agar daily_attendance bo'sh bo'lsa, mavjud barcha tarixni yig'ish"""
    db = SessionLocal()
    try:
        count = db.query(DailyAttendance).count()
        if count == 0:
            logger.info("daily_attendance bo'sh. Tarixni boshlang'ich yig'ish boshlandi...")
            first_event = db.query(Attendance).order_by(Attendance.event_time.asc()).first()
            if first_event and first_event.event_time:
                date_from = first_event.event_time.date()
                today = datetime.now(settings.tz).date()
                rebuild(db, date_from, today)
            else:
                today = datetime.now(settings.tz).date()
                rebuild(db, today, today)
    except Exception as e:
        logger.error("Boshlang'ich sinxronizatsiyada xatolik: %s", e)
    finally:
        db.close()


def start_scheduler():
    if not scheduler.running:
        # Har 5 daqiqada bugungi kun
        scheduler.add_job(
            job_rebuild_today,
            IntervalTrigger(minutes=5),
            id="job_rebuild_today",
            replace_existing=True
        )
        # Har kecha 00:30 da oxirgi 7 kun
        scheduler.add_job(
            job_rebuild_recent,
            CronTrigger(hour=0, minute=30, timezone=settings.tz),
            id="job_rebuild_recent",
            replace_existing=True
        )
        scheduler.start()
        logger.info("APScheduler muvaffaqiyatli ishga tushdi.")
        # Boshlang'ich yig'ish
        initial_sync_if_needed()


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler to'xtatildi.")
