from datetime import date, datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import require_viewer
from app.db.session import get_db
from app.services.stats import (
    get_overview, get_trend, get_ranking, get_arrival_histogram, get_heatmap
)

router = APIRouter(prefix="/stats", tags=["Statistika"], dependencies=[Depends(require_viewer)])


@router.get("/overview")
def overview_endpoint(
    day: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Bugungi yoki berilgan kundagi KPI ko'rsatkichlari"""
    return get_overview(db, day)


@router.get("/trend")
def trend_endpoint(
    days: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_db)
):
    """Oxirgi N kundagi kechikish foizi va o'rtacha kelish vaqti"""
    return get_trend(db, days)


@router.get("/ranking")
def ranking_endpoint(
    date_from: Optional[date] = Query(None, alias="from"),
    date_to: Optional[date] = Query(None, alias="to"),
    db: Session = Depends(get_db)
):
    """Eng ko'p kechikkan va eng intizomli 10 xodim"""
    today = datetime.now(settings.tz).date()
    d_from = date_from or (today - timedelta(days=30))
    d_to = date_to or today
    return get_ranking(db, d_from, d_to)


@router.get("/arrival-hist")
def arrival_hist_endpoint(
    date_from: Optional[date] = Query(None, alias="from"),
    date_to: Optional[date] = Query(None, alias="to"),
    db: Session = Depends(get_db)
):
    """Kelish vaqti gistogrammasi (vaqt intervallari bo'yicha)"""
    today = datetime.now(settings.tz).date()
    d_from = date_from or (today - timedelta(days=30))
    d_to = date_to or today
    return get_arrival_histogram(db, d_from, d_to)


@router.get("/heatmap")
def heatmap_endpoint(
    date_from: Optional[date] = Query(None, alias="from"),
    date_to: Optional[date] = Query(None, alias="to"),
    db: Session = Depends(get_db)
):
    """Hafta kuni x Soat issiqlik xaritasi"""
    today = datetime.now(settings.tz).date()
    d_from = date_from or (today - timedelta(days=30))
    d_to = date_to or today
    return get_heatmap(db, d_from, d_to)
