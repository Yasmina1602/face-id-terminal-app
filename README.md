# Davomat Tizimi: Hikvision Face ID + Telegram Bot + Web Dashboard

Ushbu tizim Hikvision yuz tanish terminali hodisalarini qabul qilish, Telegram orqali bildirishnomalar yuborish, ma'lumotlarni PostgreSQL bazasida jamlash hamda real-vaqt rejimida statistikani zamonaviy Web interfeysida ko'rsatish uchun mo'ljallangan.

---

## 🏛️ Tizim Arxitekturasi

Tizim modulli, mustaqil va mikro-servis arxitekturasi asosida qurilgan:

```
+------------------------------------+
|  Hikvision Face ID Terminali       |
|  (IP: 192.168.11.151)             |
+-----------------+------------------+
                  |
                  | 1. HTTP POST (Multipart: JSON + Yuz Rasmi)
                  v
+-----------------+------------------+
|  Telegram Bot & Webhook Servisi    |  Port: 8095
|  (Flask + python-telegram-bot)     |  Fayl: telegram_bot/main.py
+--------+------------------+--------+
         |                  |
         | 2. sendPhoto     | 3. Xom attendance + Real-time daily_attendance
         v                  v
+--------+--------+  +------+------------------------------------------+
| Telegram Guruhi |  |  PostgreSQL Ma'lumotlar Bazasi                  |
| va Adminlar     |  |  (Baza: face_id_terminal, Port: 5432)           |
+-----------------+  |  - attendance (xom hodisalar, rasm saqlanmaydi) |
                     |  - daily_attendance (yig'ma kunlik natijalar)   |
                     |  - employees, admins, chats, app_settings       |
                     +----------------------+--------------------------+
                                            ^
                                            | 4. O'qish / Yangilash
                                            v
                     +----------------------+--------------------------+
                     |  Web Backend API (FastAPI)                      |
                     |  Port: 8090 | Fayl: web/app/main.py             |
                     |  - REST API (/api/attendance, /stats, ...)      |
                     |  - APScheduler (fon hisob-kitoblari)            |
                     |  - Excel Eksport generatsiyasi                  |
                     +----------------------+--------------------------+
                                            ^
                                            | 5. JSON / Polling (5s)
                                            v
                     +----------------------+--------------------------+
                     |  Frontend Dashboard (React + TypeScript + Vite) |
                     |  Port: 3005 | Papka: frontend/src/              |
                     |  - Kunlik Davomat Jadvali (Real-vaqt)           |
                     |  - Jonli o'tishlar lentasi, Trend va Heatmap    |
                     |  - Xodimlar, Tabel va Tizim Sozlamalari         |
                     +-------------------------------------------------+
```

### Arxitektura Prinsiplari:
1. **Alohida Jarayonlar:** Telegram bot va Web API mustaqil ishlaydi. Web server to'xtasa ham, terminaldan keladigan o'tishlar bot tomonidan uzluksiz qabul qilinadi va Telegramga jo'natiladi.
2. **Real-Vaqtda Yangilanish (Zero-Lag):** Terminaldan o'tish sodir bo'lishi bilanoq, bot xom `attendance` jadvali bilan birga `daily_attendance` jadvalini ham darhol yangilaydi. Web panel har 5 soniyada yangilanishlarni avtomatik tortib oladi — qo'lda "Qayta hisoblash" tugmasini bosish shart emas!
3. **Tartiblash:** Kunlik davomat jadvalida eng oxirgi kelgan yoki ketgan xodimlar avtomatik ravishda jadvalning eng yuqori qismida ko'rsatiladi.

---

## 🔌 Portlar Ro'yxati

| Servis | Port | Vazifasi |
| :--- | :--- | :--- |
| **PostgreSQL** | `5432` | Asosiy ma'lumotlar bazasi (`face_id_terminal`) |
| **Telegram Bot / Webhook** | `8095` | Hikvision terminalidan POST qabul qilish |
| **Web Backend (FastAPI)** | `8090` | REST API va hisobot xizmati |
| **Frontend (Vite / React)** | `3005` | Veb boshqaruv paneli |

---

## 🚀 Ishga Tushirish Ketma-Ketligi

Loyihani to'g'ri ishga tushirish uchun quyidagi ketma-ketlikda amallarni bajaring:

### 1-qadam: Ma'lumotlar bazasini tayyorlash

PostgreSQL serveringiz ishlayotganligiga ishonch hosil qiling, so'ng loyiha ildizida quyidagi buyruqni bering:
```powershell
python apply_schema.py
```
*Bu buyruq `face_id_terminal` bazasi va barcha jadvallarni tekshiradi hamda standart admin foydalanuvchisini (`admin` / `admin123`) yaratadi.*

---

### 2-qadam: Telegram Bot va Hikvision tinglovchisini ishga tushirish

Terminal 1:
```powershell
cd telegram_bot
python main.py
```
*Muvaffaqiyatli ishga tushganda:*
```text
INFO 🤖 Bot va server ishga tushdi...
INFO Serving on http://0.0.0.0:8095
```

---

### 3-qadam: Web Backend API ni ishga tushirish

Terminal 2:
```powershell
cd web
uvicorn app.main:app --host 127.0.0.1 --port 8090 --reload
```
*Muvaffaqiyatli ishga tushganda:*
```text
INFO: Uvicorn running on http://127.0.0.1:8090
INFO: Application startup complete.
```
*Interaktiv API hujjatlari (Swagger): `http://127.0.0.1:8090/docs`*

---

### 4-qadam: Frontend boshqaruv panelini ishga tushirish

Terminal 3:
```powershell
cd frontend
npm run dev
```
*Brauzerda ochish:* **`http://localhost:3005`**

---

## 🔐 Standart Kirish Ma'lumotlari

- **Panel manzili:** `http://localhost:3005`
- **Login:** `admin`
- **Parol:** `admin123`

*(Tizimga kirgach, «Sozlamalar» ➡️ «Adminlar va Rollar» bo'limida yangi adminlar qo'shishingiz yoki parolni yangilashingiz mumkin).*

---

## ⚙️ Sozlamalar fayli (`telegram_bot/.env`)

Web ilova ham, bot ham sozlamalarni to'g'ridan-to'g'ri `telegram_bot/.env` dan o'qiydi:
```env
TELEGRAM_BOT_TOKEN=Sizning_Bot_Tokeningiz
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=face_id_terminal
DB_USER=root
DB_PASS=1234
PORT=8095
DEFAULT_START=09:00
GRACE_MINUTES=0
RETENTION_DAYS=180
TZ_NAME=Asia/Tashkent
```
