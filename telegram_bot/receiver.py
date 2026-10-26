import os
import json
import base64
from datetime import datetime
import requests
from requests.auth import HTTPDigestAuth
from flask import Flask, request

from config import (
    PORT, HIK_IP, HIK_USER, HIK_PASS, TZ, DEBUG_EVENTS,
    log, now_local, esc, fmt_min
)
from cache import (
    EMP, UNKNOWN_SEEN, LOCK,
    has_checkin_today, mark_checkin, calc_late, is_duplicate_event
)
import repository
from notifier import enqueue_photo

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024


def extract_image(inner: dict, data: dict) -> bytes | None:
    """
    Hikvision terminaldan kelgan yuz rasmini 3 xil usulda qidirib topadi:
    1. multipart fayl sifatida (request.files)
    2. JSON ichida Base64 ko'rinishida ('facePicBinaryData')
    3. Terminaldagi URL orqali HTTP Digest Auth bilan yuklab olish ('pictureURL')
    """
    if request.files:
        for key in request.files:
            f = request.files[key]
            if f.filename:
                return f.read()

    b64 = inner.get("facePicBinaryData") or data.get("facePicBinaryData")
    if b64:
        try:
            return base64.b64decode(b64)
        except Exception:
            pass

    pic_url = inner.get("pictureURL") or data.get("pictureURL")
    if pic_url:
        if pic_url.startswith("/"):
            pic_url = f"http://{HIK_IP}{pic_url}"
        try:
            r = requests.get(pic_url, auth=HTTPDigestAuth(HIK_USER, HIK_PASS), timeout=5)
            if r.status_code == 200:
                return r.content
        except Exception:
            pass

    return None


def _trunc(o, n=120):
    """Log uchun juda uzun Base64 yoki massivlarni qisqartirib ko'rsatish"""
    if isinstance(o, dict):
        return {k: _trunc(v, n) for k, v in o.items()}
    if isinstance(o, list):
        return [_trunc(v, n) for v in o[:10]]
    if isinstance(o, str) and len(o) > n:
        return o[:n] + f"...({len(o)} belgi)"
    return o


# ==============================================================================
# HIKVISION TERMINALIDAN KELAYOTGAN JSON MA'LUMOTLARINI QABUL QILISH JOYI:
# ==============================================================================
@app.route("/", methods=["POST"])
def hikvision_listener():
    """
    Hikvision Face ID terminal har safar xodim o'tganda (yoki yurak urishi / heartbeat yuborganda)
    ushbu manzilga HTTP POST (multipart/form-data) so'rovini yuboradi.

    Qabul qilinadigan asosiy JSON maydoni:
        request.form.get("AccessControllerEvent")

    Hikvision JSON tuzilishi (namuna):
    {
        "ipAddress": "192.168.11.151",
        "portNo": 80,
        "dateTime": "2026-10-26T09:45:30+05:00",
        "eventType": "AccessControllerEvent",
        "AccessControllerEvent": {
            "employeeNoString": "15",         # Xodimning terminaldagi ID raqami
            "name": "Aliyev Vali",           # Terminalga kiritilgan xodim ismi
            "attendanceStatus": "checkIn",    # 'checkIn' (Keldi) yoki 'checkOut' (Ketdi)
            "label": "Keldim",                # O'zbekcha / ruscha belgi
            "serialNo": 12345,                # Hodisaning ketma-ketlik raqami
            "majorEventType": 5,              # 5 = Access Control hodisasi
            "subEventType": 75,               # 75 = Yuzni muvaffaqiyatli tanish
            "pictureURL": "/ISAPI/...",       # Rasm havolasi
            "facePicBinaryData": "..."        # Ba'zi modellarda Base64 rasm
        }
    }
    """
    event_data = request.form.get("AccessControllerEvent")
    if not event_data:
        body = request.get_data(cache=True, as_text=False)[:600]
        log.debug(
            "AccessControllerEvent maydoni yo'q. content_type=%s form_keys=%s files=%s body=%r",
            request.content_type, list(request.form.keys()), list(request.files.keys()), body
        )
        return "OK", 200

    # Eshik ochildi/yopildi kabi davomatga aloqasiz signallarni o'tkazib yuborish
    if "attendanceStatus" not in event_data and '"label"' not in event_data:
        return "OK", 200

    try:
        data = json.loads(event_data)
        if data.get("eventType") == "heartBeat":
            return "OK", 200

        inner = data.get("AccessControllerEvent", {}) or {}

        # ----------------------------------------------------------------------
        # Terminaldan kelgan RAW JSON ma'lumotlarini logda ko'rish:
        # .env da DEBUG_EVENTS=1 yoki LOG_LEVEL=DEBUG bo'lsa to'liq ko'rsatiladi
        # ----------------------------------------------------------------------
        if DEBUG_EVENTS or log.isEnabledFor(10):  # 10 = logging.DEBUG
            log.info("📥 [HIKVISION RAW JSON]:\n%s", json.dumps(_trunc(data), ensure_ascii=False, indent=2))

        emp_no = str(inner.get("employeeNoString") or "").strip()
        dev_name = inner.get("name")

        log.debug(
            "EVENT: id=%r name=%r status=%r label=%r time=%r files=%s",
            emp_no, dev_name, inner.get("attendanceStatus"), inner.get("label"),
            data.get("dateTime"), list(request.files.keys())
        )

        if not emp_no and not dev_name:
            log.debug("  -> tashlandi: xodim tanilmagan (ID va ism yo'q)")
            return "OK", 200

        emp_no = emp_no or dev_name

        # Hodisa vaqtini Toshkent vaqtiga o'girish
        try:
            t = datetime.fromisoformat(data.get("dateTime", ""))
            if t.tzinfo:
                t = t.astimezone(TZ).replace(tzinfo=None)
        except Exception:
            t = now_local()

        # checkIn yoki checkOut ni aniqlash
        attendance = inner.get("attendanceStatus")
        label = inner.get("label")
        if attendance == "checkIn" or label == "Keldim":
            etype = "checkIn"
        elif attendance == "checkOut" or label == "Ketdim":
            etype = "checkOut"
        else:
            log.debug("  -> tashlandi: Keldim/Ketdim emas (status/label mos kelmadi)")
            return "OK", 200

        # Faqat keshdagi faol xodimlar uchun ishlaydi
        with LOCK:
            info = EMP.get(emp_no)

        if not info or not info["active"]:
            log.debug("  -> tashlandi: ro'yxatda yo'q yoki nofaol (ID %s)", emp_no)
            if not info:
                UNKNOWN_SEEN[emp_no] = dev_name or ""
                if len(UNKNOWN_SEEN) > 50:
                    UNKNOWN_SEEN.pop(next(iter(UNKNOWN_SEEN)))
            return "OK", 200

        name = info["name"]

        # Yuz rasmini olish
        image = extract_image(inner, data)
        if not image:
            log.debug("  -> tashlandi: rasm topilmadi")
            return "OK", 200

        # 30 soniya ichidagi takroriy signallarni tashlab yuborish
        if is_duplicate_event(emp_no, etype, t, window_sec=30):
            log.debug("  -> tashlandi: 30 soniya ichida takroriy signal")
            return "OK", 200

        # Kechikish va holatni aniqlash
        late = 0
        if etype == "checkIn":
            if has_checkin_today(emp_no, t.date()):
                status = "Qayta o'tish 🔁"
            else:
                late = calc_late(t, info["start"])
                status = "Kech keldi ⚠️" if late > 0 else "Vaqtida keldi ✅"
        else:
            status = "Ketdi 🚶‍♂️"

        serial_no = inner.get("serialNo")
        try:
            serial_no = int(serial_no) if serial_no is not None else None
        except Exception:
            serial_no = None

        # Bazaga saqlash
        try:
            repository.save_event(emp_no, name, etype, t, late, serial_no=serial_no)
        except Exception as e:
            log.error("Bazaga yozishda xato: %s", e)

        # Telegram xabar matni
        caption = (
            f"🚪 {status}\n👤 Ism-familiya: {esc(name)}\n"
            f"📅 Sana: {t:%d.%m.%Y}\n🕐 Vaqt: {t:%H:%M:%S}"
        )
        if etype == "checkIn":
            caption += f"\n⏰ Ish boshlanishi: {info['start']:%H:%M}"
        if late > 0:
            caption += f"\n⚠️ Kechikish: {fmt_min(late)}"

        if etype == "checkIn":
            mark_checkin(emp_no, t.date())

        log.info("✔ %s | %s | %s | kechikish=%s", name, etype, f"{t:%H:%M:%S}", late)
        enqueue_photo(caption, image)

    except Exception as e:
        log.exception("Webhook qabul qilishda xatolik: %s", e)

    return "OK", 200


def run_receiver():
    """Hikvision HTTP serverini ishga tushirish (Waitress orqali)"""
    log.info("Hikvision listener %d-portda ishga tushmoqda...", PORT)
    try:
        from waitress import serve
        serve(app, host="0.0.0.0", port=PORT, threads=4)
    except ImportError:
        app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False, threaded=True)
