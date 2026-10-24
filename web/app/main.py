import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.jobs.scheduler import start_scheduler, stop_scheduler
from app.api.auth import router as auth_router
from app.api.stats import router as stats_router
from app.api.events import router as events_router
from app.api.employees import router as employees_router
from app.api.attendance import router as attendance_router
from app.api.reports import router as reports_router
from app.api.admins import router as admins_router
from app.api.chats import router as chats_router
from app.api.settings import router as settings_router
from app.api.audit import router as audit_router
from app.api.health import router as health_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
log = logging.getLogger("web")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Davomat Web API ishga tushmoqda...")
    try:
        start_scheduler()
    except Exception as e:
        log.warning("Scheduler ishga tushirishda ogohlantirish: %s", e)
    yield
    log.info("Davomat Web API to'xtatilmoqda...")
    try:
        stop_scheduler()
    except Exception as e:
        log.warning("Scheduler to'xtatishda ogohlantirish: %s", e)


app = FastAPI(
    title="Davomat Tizimi API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Xatoliklar uchun standart format: {"error": {"code": ..., "message": ...}}
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.exception("Global xatolik: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": str(exc)
            }
        }
    )


# API marshrutlari
api_prefix = "/api"
app.include_router(auth_router, prefix=api_prefix)
app.include_router(stats_router, prefix=api_prefix)
app.include_router(events_router, prefix=api_prefix)
app.include_router(employees_router, prefix=api_prefix)
app.include_router(attendance_router, prefix=api_prefix)
app.include_router(reports_router, prefix=api_prefix)
app.include_router(admins_router, prefix=api_prefix)
app.include_router(chats_router, prefix=api_prefix)
app.include_router(settings_router, prefix=api_prefix)
app.include_router(audit_router, prefix=api_prefix)
app.include_router(health_router, prefix=api_prefix)


# Statik fayllar (Frontend React build: dist/)
dist_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dist")
if not os.path.exists(dist_dir):
    frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")
    if os.path.exists(frontend_dist):
        dist_dir = frontend_dist

if os.path.exists(dist_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(dist_dir, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(dist_dir, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(dist_dir, "index.html"))
else:
    @app.get("/")
    def index_placeholder():
        return {
            "message": "Davomat Tizimi API ishlamoqda. Hujjatlar: /docs",
            "version": "1.0.0"
        }
