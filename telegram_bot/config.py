import os
import re
import html
import logging
from datetime import datetime, time
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv()

# Logging sozlamalari
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
for _n in ("httpx", "httpcore", "urllib3", "werkzeug", "waitress", "apscheduler"):
    logging.getLogger(_n).setLevel(logging.WARNING)

log = logging.getLogger("davomat")

# Telegram sozlamalari
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_CHAT_IDS = [x.strip() for x in os.getenv("TELEGRAM_CHAT_ID", "").split(",") if x.strip()]
SUPER_ADMINS = {int(x) for x in os.getenv("ADMIN_IDS", "").replace(" ", "").split(",") if x}

# Hikvision terminal sozlamalari
HIK_IP = os.getenv("HIKVISION_IP")
HIK_USER = os.getenv("HIKVISION_USER")
HIK_PASS = os.getenv("HIKVISION_PASSWORD")
PORT = int(os.getenv("PORT", "8080"))
DEBUG_EVENTS = os.getenv("DEBUG_EVENTS", "0") == "1"

# Ma'lumotlar bazasi (PostgreSQL)
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "face_id_terminal")
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "1234")

# Ish vaqti va tizim qoidalari
TZ_NAME = os.getenv("TZ_NAME", "Asia/Tashkent")
TZ = ZoneInfo(TZ_NAME)
GRACE_MINUTES = int(os.getenv("GRACE_MINUTES", "0"))
RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "180"))
WEEKEND_DAYS = {int(x) for x in os.getenv("WEEKEND_DAYS", "6").split(",") if x.strip()}

WEEKDAYS = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]


def parse_hhmm(s: str):
    """'8:30', '08.30' yoki '8' ko'rinishidagi vaqtni datetime.time ga o'giradi"""
    if not s:
        return None
    s = s.strip().replace(".", ":")
    m = re.fullmatch(r"(\d{1,2})(?::(\d{1,2}))?", s)
    if not m:
        return None
    h, mi = int(m.group(1)), int(m.group(2) or 0)
    if h > 23 or mi > 59:
        return None
    return time(h, mi)


DEFAULT_START = parse_hhmm(os.getenv("DEFAULT_START", "09:00")) or time(9, 0)


def now_local() -> datetime:
    """Toshkent vaqti bo'yicha joriy datetime (tz-naive)"""
    return datetime.now(TZ).replace(tzinfo=None)


def esc(s) -> str:
    """Telegram HTML xabarlar uchun belgilarni escape qilish"""
    return html.escape(str(s or ""))


def fmt_min(m) -> str:
    """Daqiqalarni chiroyli matn shaklida formatlash"""
    m = int(m or 0)
    return f"{m} daq" if m < 60 else f"{m // 60} soat {m % 60} daq"
