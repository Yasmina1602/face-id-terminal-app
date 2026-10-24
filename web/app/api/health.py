from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.jobs.scheduler import scheduler

router = APIRouter(prefix="", tags=["Tizim Holati"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    scheduler_ok = scheduler.running if scheduler else False

    return {
        "status": "healthy" if db_ok else "unhealthy",
        "database": "connected" if db_ok else "disconnected",
        "scheduler": "running" if scheduler_ok else "stopped"
    }
