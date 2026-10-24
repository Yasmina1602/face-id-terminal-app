from datetime import date, datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import require_viewer
from app.db.session import get_db
from app.services.reports import export_employee_report, export_summary_report

router = APIRouter(prefix="/reports", tags=["Hisobotlar"], dependencies=[Depends(require_viewer)])


@router.get("/employee/{emp_no}/export")
def get_employee_excel_export(
    emp_no: str,
    date_from: Optional[date] = Query(None, alias="from"),
    date_to: Optional[date] = Query(None, alias="to"),
    db: Session = Depends(get_db)
):
    today = datetime.now(settings.tz).date()
    d_from = date_from or date(today.year, today.month, 1)
    d_to = date_to or today

    if (d_to - d_from).days > 366:
        raise HTTPException(status_code=400, detail="Maksimal davr 366 kun")

    buf, filename = export_employee_report(db, emp_no, d_from, d_to)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/summary/export")
def get_summary_excel_export(
    date_from: Optional[date] = Query(None, alias="from"),
    date_to: Optional[date] = Query(None, alias="to"),
    db: Session = Depends(get_db)
):
    today = datetime.now(settings.tz).date()
    d_from = date_from or date(today.year, today.month, 1)
    d_to = date_to or today

    if (d_to - d_from).days > 366:
        raise HTTPException(status_code=400, detail="Maksimal davr 366 kun")

    buf, filename = export_summary_report(db, d_from, d_to)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
