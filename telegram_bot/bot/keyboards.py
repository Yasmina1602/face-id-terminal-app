from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup

B_TODAY = "📅 Bugungi hisobot"
B_WEEK = "📊 Haftalik hisobot"
B_EXCEL = "📥 Excel hisobot"
B_EMPS = "👥 Xodimlar"
B_ADD_EMP = "➕ Xodim qo'shish"
B_ADMIN = "⚙️ Admin panel"

MENU_BUTTONS = {B_TODAY, B_WEEK, B_EXCEL, B_EMPS, B_ADD_EMP, B_ADMIN}

MAIN_KB = ReplyKeyboardMarkup(
    [[B_TODAY, B_WEEK], [B_EXCEL, B_EMPS], [B_ADD_EMP, B_ADMIN]],
    resize_keyboard=True
)


def ikb(rows):
    """Inline tugmalar klaviaturasi yasash yordamchisi"""
    return InlineKeyboardMarkup([[InlineKeyboardButton(t, callback_data=d) for t, d in r] for r in rows])


def period_kb(scope: str):
    """Excel hisoboti uchun muddat tanlash tugmalari"""
    return ikb([
        [("Bugun", f"per:{scope}:1"), ("7 kun", f"per:{scope}:7")],
        [("30 kun", f"per:{scope}:30"), ("Shu oy", f"per:{scope}:m0")],
        [("O'tgan oy", f"per:{scope}:m1"), ("📝 Sana kiritish", f"per:{scope}:c")],
    ])
