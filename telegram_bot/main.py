"""
=============================================================================
Face ID Terminal & Telegram Bot Davomat Tizimi
Asosiy ishga tushirish fayli (Entrypoint)
=============================================================================
Modullar tuzilishi:
  - config.py      : Sozlamalar (.env), konstantalar va vaqt yordamchilari
  - database.py    : PostgreSQL connection pool va jadvallar migratsiyasi
  - cache.py       : Tezkor xotira (RAM) keshi va sinxronizatsiya
  - repository.py  : Ma'lumotlar bazasi so'rovlari va amallari
  - notifier.py    : Telegramga rasmli xabarlar navbati (Queue + Worker)
  - receiver.py    : Hikvision Face ID terminalidan JSON va rasmni qabul qilish
  - reports.py     : Matnli va Excel hisobotlarini shakllantirish
  - bot/           : Telegram bot handlerlari, tugmalari va bot sozlamalari
=============================================================================
"""

import threading
from telegram import Update

from config import log
from database import init_db
from cache import load_caches
from notifier import tg_worker
from receiver import run_receiver
from bot.setup import create_bot_app


def main():
    log.info("Davomat tizimi ishga tushmoqda...")

    # 1. Ma'lumotlar bazasi jadvallarini tekshirish/yaratish
    init_db()

    # 2. Xodimlar, adminlar va chatlar keshini xotiraga yuklash
    load_caches()

    # 3. Telegramga rasm yuboruvchi fon oqimini ishga tushirish
    threading.Thread(target=tg_worker, name="TgWorkerThread", daemon=True).start()

    # 4. Hikvision terminalidan signallarni qabul qiluvchi HTTP serverini ishga tushirish
    threading.Thread(target=run_receiver, name="HikvisionReceiverThread", daemon=True).start()

    # 5. Telegram bot ilovasini yaratish va polling rejimida ishga tushirish
    app = create_bot_app()
    log.info("🤖 Telegram bot va Hikvision listener muvaffaqiyatli ishga tushdi.")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
