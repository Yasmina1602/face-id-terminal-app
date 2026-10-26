from datetime import time
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ChatMemberHandler, filters
)

from config import TG_TOKEN, TZ
from bot.handlers import (
    start, cmd_new, on_text, on_callback, on_my_chat_member,
    on_error, cleanup_job, check_config_job
)


def create_bot_app() -> Application:
    """Telegram Application ni yaratish va barcha handlerlar va rejalashtirilgan vazifalarni ro'yxatdan o'tkazish"""
    app = Application.builder().token(TG_TOKEN).build()
    private = filters.ChatType.PRIVATE

    app.add_handler(CommandHandler("start", start, filters=private))
    app.add_handler(CommandHandler("yangi", cmd_new, filters=private))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & private, on_text))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(ChatMemberHandler(on_my_chat_member, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_error_handler(on_error)

    if app.job_queue:
        # Har kuni soat 03:00 da eski yozuvlarni tozalash
        app.job_queue.run_daily(cleanup_job, time=time(3, 0, tzinfo=TZ))
        # Har 30 soniyada konfiguratsiya o'zgarishini tekshirish
        app.job_queue.run_repeating(check_config_job, interval=30, first=15)

    return app
