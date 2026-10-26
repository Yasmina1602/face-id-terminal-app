import queue
import requests
from config import TG_TOKEN, TG_CHAT_IDS, SUPER_ADMINS, log
from cache import CHATS, ADMINS, LOCK

SEND_Q = queue.Queue(maxsize=50)


def tg_targets():
    """Xabarlar yuborilishi kerak bo'lgan barcha Telegram chat / guruh ID lari"""
    with LOCK:
        groups = list(CHATS)
    targets = list(dict.fromkeys(TG_CHAT_IDS + [str(g) for g in groups]))
    if not targets:
        with LOCK:
            targets = [str(a) for a in (SUPER_ADMINS | ADMINS)]
        if not targets:
            log.warning("Xabar yuboradigan chat yo'q: TELEGRAM_CHAT_ID yoki ADMIN_IDS ni to'ldiring")
    return targets


def tg_worker():
    """
    Bitta fon oqimi navbatdan oladi.
    Rasm Telegram serveriga faqat bir marta yuklanadi, 
    qolgan chatlarga file_id orqali tezkor yuboriladi.
    """
    session = requests.Session()
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"

    while True:
        caption, img = SEND_Q.get()
        try:
            file_id = None
            for chat in tg_targets():
                try:
                    data = {"chat_id": chat, "caption": caption, "parse_mode": "HTML"}
                    if file_id:
                        data["photo"] = file_id
                        r = session.post(url, data=data, timeout=15)
                    else:
                        r = session.post(url, data=data, files={"photo": ("face.jpg", img)}, timeout=25)
                    j = r.json()
                    if j.get("ok"):
                        log.debug("  -> Telegramga yuborildi: %s", chat)
                        if not file_id:
                            file_id = j["result"]["photo"][-1]["file_id"]
                    else:
                        log.warning("Telegram xato (%s): %s", chat, j.get("description"))
                except Exception as e:
                    log.warning("Yuborishda xato (%s): %s", chat, e)
        finally:
            SEND_Q.task_done()


def enqueue_photo(caption: str, img: bytes):
    """Rasmli xabarni yuborish navbatiga qo'shish"""
    try:
        SEND_Q.put_nowait((caption, img))
    except queue.Full:
        log.warning("Telegram yuborish navbati to'lgan, xabar tashlab yuborildi")
