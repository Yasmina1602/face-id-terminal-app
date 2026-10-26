import threading
from datetime import datetime, date, time, timedelta

from config import SUPER_ADMINS, GRACE_MINUTES, log
import repository

EMP = {}        # emp_no -> {"name": str, "start": time, "active": bool}
ADMINS = set()  # tg_id to'plami
CHATS = set()   # chat_id to'plami
UNKNOWN_SEEN = {}  # {emp_no: dev_name}
_last_config_version = 0
_ci = {"day": None, "ids": set()}
_last_event = {}   # (emp_no, type) -> datetime

LOCK = threading.Lock()
_ci_lock = threading.Lock()


def load_caches():
    """Dastur ishga tushganda bazadan keshni yuklash"""
    global _last_config_version
    emps = repository.fetch_all_employees()
    admins = repository.fetch_all_admins()
    chats = repository.fetch_all_chats()
    ver = repository.fetch_config_version()

    with LOCK:
        _last_config_version = ver
        EMP.clear()
        EMP.update(emps)
        ADMINS.clear()
        ADMINS.update(admins)
        CHATS.clear()
        CHATS.update(chats)
    log.info("Kesh yuklandi: %d xodim, %d admin, %d chat (versiya: %d)",
             len(emps), len(admins), len(chats), ver)


def check_config_version():
    """Web panel yoki botdan xodimlar/adminlar o'zgarganini 30 soniyada tekshirib yangilash"""
    global _last_config_version
    try:
        ver = repository.fetch_config_version()
        if ver != _last_config_version:
            log.info("Config versiyasi yangilandi (%s -> %s), keshlar qayta yuklanmoqda...",
                     _last_config_version, ver)
            emps = repository.fetch_all_employees()
            admins = repository.fetch_all_admins()
            chats = repository.fetch_all_chats()
            with LOCK:
                _last_config_version = ver
                EMP.clear()
                EMP.update(emps)
                ADMINS.clear()
                ADMINS.update(admins)
                CHATS.clear()
                CHATS.update(chats)
    except Exception as e:
        log.warning("Config versiya tekshirishda xatolik: %s", e)


def is_admin(uid: int) -> bool:
    """Foydalanuvchi super admin yoki oddiy admin ekanligini tekshirish"""
    with LOCK:
        return uid in SUPER_ADMINS or uid in ADMINS


def has_checkin_today(emp_no: str, d: date) -> bool:
    """Xodim bugun avvalroq kelganligini tezkor tekshirish (kunda 1 marta DB dan, keyin RAM dan)"""
    with _ci_lock:
        if _ci["day"] != d:
            _ci["ids"] = repository.fetch_today_checkin_ids(d)
            _ci["day"] = d
        return emp_no in _ci["ids"]


def mark_checkin(emp_no: str, d: date):
    """Xodimni bugungi kelganlar keshiga qo'shish"""
    with _ci_lock:
        if _ci["day"] == d:
            _ci["ids"].add(emp_no)


def calc_late(t: datetime, start: time) -> int:
    """Belgilangan ish vaqtidan necha daqiqa kechikkanini hisoblash"""
    base = datetime.combine(t.date(), start)
    if t <= base + timedelta(minutes=GRACE_MINUTES):
        return 0
    return max(1, int((t - base).total_seconds() // 60))


def is_duplicate_event(emp_no: str, etype: str, t: datetime, window_sec: int = 30) -> bool:
    """30 soniya ichida kelgan takroriy signallarni filtrlash"""
    key = (emp_no, etype)
    prev = _last_event.get(key)
    if prev and abs((t - prev).total_seconds()) < window_sec:
        return True
    if len(_last_event) > 500:
        _last_event.clear()
    _last_event[key] = t
    return False
