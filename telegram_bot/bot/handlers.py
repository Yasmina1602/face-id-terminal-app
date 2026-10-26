import re
import asyncio
from datetime import datetime, timedelta
from telegram import Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from config import (
    DEFAULT_START, SUPER_ADMINS, log, now_local, esc, parse_hhmm
)
from cache import (
    EMP, UNKNOWN_SEEN, LOCK,
    is_admin, check_config_version
)
import repository
from reports import today_text, weekly_text, build_excel
from bot.keyboards import (
    B_TODAY, B_WEEK, B_EXCEL, B_EMPS, B_ADD_EMP, B_ADMIN,
    MENU_BUTTONS, MAIN_KB, ikb, period_kb
)

XL_SEM = asyncio.Semaphore(1)


async def reply_long(msg, text: str, **kw):
    """Telegramning 4096 belgili limitidan oshib ketgan xabarlarni bo'lib yuborish"""
    chunk = ""
    for line in text.split("\n"):
        if len(chunk) + len(line) + 1 > 3800:
            await msg.reply_text(chunk, parse_mode="HTML", **kw)
            chunk = ""
        chunk += line + "\n"
    if chunk.strip():
        await msg.reply_text(chunk, parse_mode="HTML", **kw)


def period_range(p: str):
    """Tugma kodi ('1', '7', '30', 'm0', 'm1') bo'yicha (boshlanish, tugash) sanalarini olish"""
    today = now_local().date()
    if p == "1":
        return today, today
    if p == "7":
        return today - timedelta(days=6), today
    if p == "30":
        return today - timedelta(days=29), today
    if p == "m0":
        return today.replace(day=1), today
    if p == "m1":
        last = today.replace(day=1) - timedelta(days=1)
        return last.replace(day=1), last
    return None


def parse_dates(text: str):
    """Matn ichidagi sanalarni ajratib olish (masalan, 01.10.2026 - 22.10.2026)"""
    found = re.findall(r"\d{1,4}[./-]\d{1,2}[./-]\d{1,4}", text)
    out = []
    for f in found[:2]:
        for fmt in ("%d.%m.%Y", "%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%Y.%m.%d"):
            try:
                out.append(datetime.strptime(f, fmt).date())
                break
            except ValueError:
                continue
    if len(out) == 1:
        out.append(out[0])
    if len(out) != 2:
        return None
    return (out[0], out[1]) if out[0] <= out[1] else (out[1], out[0])


async def send_excel(context: ContextTypes.DEFAULT_TYPE, chat_id: int, scope: str, start_d, end_d):
    """Excel faylini tayyorlab Telegramga jo'natish"""
    if (end_d - start_d).days > 366:
        await context.bot.send_message(chat_id, "❌ Muddat 1 yildan oshmasligi kerak.")
        return
    async with XL_SEM:
        emp_no = None if scope == "all" else scope
        buf, fname = await asyncio.to_thread(build_excel, start_d, end_d, emp_no)
    await context.bot.send_document(
        chat_id, document=buf, filename=fname,
        caption=f"📥 {start_d:%d.%m.%Y} — {end_d:%d.%m.%Y}"
    )


async def show_employees(msg):
    """Xodimlar ro'yxatini inline tugmalar shaklida chiqarish"""
    with LOCK:
        items = sorted(((k, v) for k, v in EMP.items() if v["active"]), key=lambda x: x[1]["name"])
    if not items:
        await msg.reply_text("Hozircha xodimlar yo'q. «➕ Xodim qo'shish» ni bosing.")
        return
    rows, row = [], []
    for k, v in items[:60]:
        row.append((f"{v['name']} • {v['start']:%H:%M}", f"emp:{k}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    extra = f"\n(Dastlabki 60 tasi ko'rsatildi, jami {len(items)})" if len(items) > 60 else ""
    await msg.reply_text("👥 Xodimni tanlang:" + extra, reply_markup=ikb(rows))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start komandasi"""
    uid = update.effective_user.id
    if not is_admin(uid):
        await update.message.reply_text(
            f"⛔ Sizda ruxsat yo'q.\nSizning Telegram ID: {uid}\nShu ID ni admin'ga yuboring."
        )
        return
    context.user_data.clear()
    await update.message.reply_text("Xush kelibsiz! Kerakli bo'limni tanlang:", reply_markup=MAIN_KB)


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Foydalanuvchi yozgan barcha matnli xabarlarni qayta ishlash"""
    uid = update.effective_user.id
    if not is_admin(uid):
        await update.message.reply_text(f"⛔ Ruxsat yo'q. Sizning ID: {uid}")
        return

    text = (update.message.text or "").strip()
    ud = context.user_data
    msg = update.message

    if text in MENU_BUTTONS:
        ud.pop("state", None)
        if text == B_TODAY:
            await reply_long(msg, await asyncio.to_thread(today_text))
        elif text == B_WEEK:
            t = await asyncio.to_thread(weekly_text)
            await msg.reply_text(t, parse_mode="HTML", reply_markup=ikb([[("🔄 Yangilash", "refresh_weekly")]]))
        elif text == B_EXCEL:
            await msg.reply_text(
                "📥 Qaysi hisobot kerak?",
                reply_markup=ikb([[("👥 Barcha xodimlar", "xl_all"), ("👤 Bitta xodim", "xl_one")]])
            )
        elif text == B_EMPS:
            await show_employees(msg)
        elif text == B_ADD_EMP:
            ud["state"] = "add_emp"
            await msg.reply_text(
                "Xodim ma'lumotini shu formatda yuboring:\n\n"
                "<code>ID | Ism Familiya | Ish boshlanishi</code>\n"
                "Masalan: <code>15 | Aliyev Vali | 8:30</code>\n\n"
                "ID — Hikvision qurilmasidagi xodim raqami. Vaqt yozilmasa "
                f"{DEFAULT_START:%H:%M} qo'yiladi.",
                parse_mode="HTML"
            )
        elif text == B_ADMIN:
            await msg.reply_text(
                "⚙️ Admin panel",
                reply_markup=ikb([
                    [("➕ Admin qo'shish", "adm_add"), ("➖ Admin o'chirish", "adm_del")],
                    [("📋 Adminlar ro'yxati", "adm_list")]
                ])
            )
        return

    state = ud.get("state")
    if state == "add_emp":
        parts = [p.strip() for p in text.split("|")]
        if len(parts) < 2 or not parts[0] or not parts[1]:
            await msg.reply_text("❌ Format noto'g'ri. Masalan: 15 | Aliyev Vali | 8:30")
            return
        start_t = parse_hhmm(parts[2]) if len(parts) > 2 else DEFAULT_START
        if not start_t:
            await msg.reply_text("❌ Vaqt noto'g'ri. Masalan: 8:30")
            return
        await asyncio.to_thread(repository.upsert_employee, parts[0], parts[1], start_t)
        with LOCK:
            EMP[parts[0]] = {"name": parts[1], "start": start_t, "active": True}
        ud.pop("state", None)
        await msg.reply_text(f"✅ Qo'shildi: {parts[1]} (ID {parts[0]}), ish boshlanishi {start_t:%H:%M}")

    elif state == "set_time":
        t = parse_hhmm(text)
        if not t:
            await msg.reply_text("❌ Vaqt noto'g'ri. Masalan: 8 yoki 8:30")
            return
        emp_no = ud.pop("emp_no", None)
        ud.pop("state", None)
        await asyncio.to_thread(repository.set_work_start, emp_no, t)
        with LOCK:
            if emp_no in EMP:
                EMP[emp_no]["start"] = t
        await msg.reply_text(f"✅ Ish boshlanish vaqti {t:%H:%M} qilib belgilandi.")

    elif state == "add_admin":
        parts = [p.strip() for p in text.split("|")]
        if not parts[0].lstrip("-").isdigit():
            await msg.reply_text("❌ Faqat raqamli Telegram ID yuboring. Masalan: 123456789 | Ism")
            return
        admin_id = int(parts[0])
        admin_name = parts[1] if len(parts) > 1 else ""
        await asyncio.to_thread(repository.add_admin, admin_id, admin_name)
        with LOCK:
            from cache import ADMINS
            ADMINS.add(admin_id)
        ud.pop("state", None)
        await msg.reply_text("✅ Admin qo'shildi.")

    elif state == "xl_range":
        rng = parse_dates(text)
        if not rng:
            await msg.reply_text("❌ Sana noto'g'ri. Masalan: 01.10.2026 - 22.10.2026")
            return
        scope = ud.pop("xl_scope", "all")
        ud.pop("state", None)
        await msg.reply_text("⏳ Hisobot tayyorlanmoqda...")
        await send_excel(context, msg.chat_id, scope, *rng)

    else:
        await msg.reply_text("Menyudan tanlang 👇", reply_markup=MAIN_KB)


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inline tugmalar bosilganda ishlovchi handler"""
    q = update.callback_query
    if not is_admin(q.from_user.id):
        await q.answer("Ruxsat yo'q", show_alert=True)
        return
    await q.answer()
    data, ud = q.data, context.user_data
    chat_id = q.message.chat_id

    if data == "refresh_weekly":
        t = await asyncio.to_thread(weekly_text)
        try:
            await q.edit_message_text(
                t + f"\n🕐 {now_local():%H:%M:%S}", parse_mode="HTML",
                reply_markup=ikb([[("🔄 Yangilash", "refresh_weekly")]])
            )
        except BadRequest:
            pass

    # ---- Excel ----
    elif data == "xl_all":
        await q.edit_message_text("📅 Muddatni tanlang (barcha xodimlar):", reply_markup=period_kb("all"))

    elif data == "xl_one":
        with LOCK:
            items = sorted(((k, v) for k, v in EMP.items() if v["active"]), key=lambda x: x[1]["name"])
        if not items:
            await q.edit_message_text("Xodimlar yo'q.")
            return
        rows, row = [], []
        for k, v in items[:60]:
            row.append((v["name"], f"xlp:{k}"))
            if len(row) == 2:
                rows.append(row)
                row = []
        if row:
            rows.append(row)
        await q.edit_message_text("👤 Xodimni tanlang:", reply_markup=ikb(rows))

    elif data.startswith("xlp:"):
        await q.edit_message_text("📅 Muddatni tanlang:", reply_markup=period_kb(data[4:]))

    elif data.startswith("per:"):
        _, scope, p = data.split(":", 2)
        if p == "c":
            ud["state"], ud["xl_scope"] = "xl_range", scope
            await q.edit_message_text("📝 Sanalarni yuboring. Masalan:\n01.10.2026 - 22.10.2026")
            return
        rng = period_range(p)
        await q.edit_message_text("⏳ Hisobot tayyorlanmoqda...")
        await send_excel(context, chat_id, scope, *rng)

    # ---- Xodim kartasi ----
    elif data.startswith("emp:"):
        no = data[4:]
        with LOCK:
            v = EMP.get(no)
        if not v:
            await q.edit_message_text("Topilmadi.")
            return
        await q.edit_message_text(
            f"👤 {v['name']}\n🆔 ID: {no}\n⏰ Ish boshlanishi: {v['start']:%H:%M}",
            reply_markup=ikb([
                [("⏰ Vaqtni o'zgartirish", f"wt:{no}")],
                [("📥 Excel", f"xlp:{no}"), ("🗑 O'chirish", f"del:{no}")]
            ])
        )

    elif data.startswith("wt:"):
        ud["state"], ud["emp_no"] = "set_time", data[3:]
        await q.edit_message_text("⏰ Yangi ish boshlanish vaqtini yuboring (masalan: 8 yoki 8:30):")

    elif data.startswith("del:"):
        emp_to_del = data[4:]
        await asyncio.to_thread(repository.set_active, emp_to_del, False)
        with LOCK:
            if emp_to_del in EMP:
                EMP[emp_to_del]["active"] = False
        await q.edit_message_text("🗑 Xodim o'chirildi (hisobotlarda va xabarlarda ko'rinmaydi).")

    # ---- Adminlar ----
    elif data == "adm_add":
        ud["state"] = "add_admin"
        await q.edit_message_text(
            "Yangi adminning Telegram ID sini yuboring:\n<code>123456789 | Ism</code>\n\n"
            "ID ni bilish uchun u botga /start yozsa, bot ID sini ko'rsatadi.",
            parse_mode="HTML"
        )

    elif data == "adm_list":
        rows = await asyncio.to_thread(repository.list_admins)
        t = "👮 <b>Adminlar:</b>\n" + "\n".join(f"• {i} {esc(n)}" for i, n in rows)
        if SUPER_ADMINS:
            t += "\n\n🔒 Asosiy: " + ", ".join(map(str, SUPER_ADMINS))
        await q.edit_message_text(t, parse_mode="HTML")

    elif data == "adm_del":
        rows = await asyncio.to_thread(repository.list_admins)
        if not rows:
            await q.edit_message_text("O'chiriladigan admin yo'q.")
            return
        await q.edit_message_text(
            "Qaysi adminni o'chirasiz?",
            reply_markup=ikb([[(f"{n or i} ({i})", f"rma:{i}")] for i, n in rows])
        )

    elif data.startswith("rma:"):
        adm_to_del = int(data[4:])
        await asyncio.to_thread(repository.remove_admin, adm_to_del)
        with LOCK:
            from cache import ADMINS
            ADMINS.discard(adm_to_del)
        await q.edit_message_text("✅ Admin o'chirildi.")


async def cmd_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/yangi komandasi: Qurilmadan o'tgan, lekin tizimga qo'shilmagan noma'lum ID larni ko'rish"""
    if not is_admin(update.effective_user.id):
        return
    if not UNKNOWN_SEEN:
        await update.message.reply_text("Ro'yxatda yo'q yangi ID kelmagan.")
        return
    t = "🆕 Qurilmadan kelgan, lekin ro'yxatda yo'q ID lar:\n\n"
    t += "\n".join(f"<code>{esc(k)} | {esc(v or 'Ism')}</code>" for k, v in UNKNOWN_SEEN.items())
    t += "\n\nQo'shish uchun «➕ Xodim qo'shish» ni bosib, shu qatorni yuboring."
    await reply_long(update.message, t)


async def on_my_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot guruhga qo'shilsa yoki guruhdan chiqarilsa ishlovchi handler"""
    cm = update.my_chat_member
    chat = cm.chat
    if chat.type not in ("group", "supergroup"):
        return
    status = cm.new_chat_member.status
    if status in ("member", "administrator"):
        if not is_admin(cm.from_user.id):
            await context.bot.leave_chat(chat.id)
            return
        await asyncio.to_thread(repository.add_chat, chat.id, chat.title)
        with LOCK:
            from cache import CHATS
            CHATS.add(chat.id)
        await context.bot.send_message(chat.id, "✅ Bot ulandi. Xodimlar davomati shu guruhga yuboriladi.")
    elif status in ("left", "kicked"):
        await asyncio.to_thread(repository.remove_chat, chat.id)
        with LOCK:
            from cache import CHATS
            CHATS.discard(chat.id)


async def check_config_job(context: ContextTypes.DEFAULT_TYPE):
    await asyncio.to_thread(check_config_version)


async def cleanup_job(context: ContextTypes.DEFAULT_TYPE):
    await asyncio.to_thread(repository.cleanup_old)


async def on_error(update, context: ContextTypes.DEFAULT_TYPE):
    log.error("Bot xatosi: %s", context.error)
