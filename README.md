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

## 📁 Konfiguratsiya Fayllari (`.env`)

Loyiha xavfsizligi yuzasidan shaxsiy parollar va tokenlar Git omboriga yuklanmaydi. Loyihani yuklab olgan kishi quyidagi `.env` fayllarini namunalardan nusxa olib yaratishi kerak.

### 1. Telegram Bot uchun: `telegram_bot/.env`
Namunadan nusxa ko'chirish:
```powershell
# Windows PowerShell:
Copy-Item telegram_bot\env.example telegram_bot\.env

# Linux / Mac:
cp telegram_bot/env.example telegram_bot/.env
```

`telegram_bot/.env` fayli ichidagi parametrlar:
```env
# Telegram bot tokeni (@BotFather orqali olinadi)
TELEGRAM_BOT_TOKEN=8747973146:AAEJVvqSyPXtMBVwW8ncUiZHqfCM7udFZvM

# Rasm va xabarlar boradigan guruh ID si (ixtiyoriy, masalan: -100123456789)
TELEGRAM_CHAT_ID=

# Asosiy adminlarning Telegram ID raqamlari (vergul bilan: 12345678,87654321)
ADMIN_IDS=

# Hikvision terminal sozlamalari
HIKVISION_IP=192.168.11.151
HIKVISION_USER=admin
HIKVISION_PASSWORD=4UnsurAsr21$

# Webhook qabul qiluvchi port (Hikvision shu portga so'rov yuboradi)
PORT=8095

# PostgreSQL ulanish sozlamalari
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=face_id_terminal
DB_USER=root
DB_PASS=1234

# Ish vaqti parametrlari
DEFAULT_START=08:00
GRACE_MINUTES=0
RETENTION_DAYS=180
WEEKEND_DAYS=6
TZ_NAME=Asia/Tashkent
LOG_LEVEL=INFO
```

---

### 2. Web Backend uchun: `web/.env.web`
Namunadan nusxa ko'chirish:
```powershell
# Windows PowerShell:
Copy-Item web\.env.web.example web\.env.web

# Linux / Mac:
cp web/.env.web.example web/.env.web
```

`web/.env.web` fayli ichidagi parametrlar:
```env
APP_ENV=development
SECRET_KEY=super-secret-key-change-in-production-davomat-2026
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=720

# PostgreSQL ulanish sozlamalari (telegram_bot/.env bilan bir xil)
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=face_id_terminal
DB_USER=root
DB_PASS=1234
DB_POOL_SIZE=3
DB_MAX_OVERFLOW=2

# Bot Token (Telegram Login widget tekshiruvi uchun)
TELEGRAM_BOT_TOKEN=8747973146:AAEJVvqSyPXtMBVwW8ncUiZHqfCM7udFZvM

# Vaqt mintaqasi
TZ_NAME=Asia/Tashkent

# Web server porti
WEB_PORT=8090
WEB_HOST=0.0.0.0
```

---

## 🚀 Loyihani Noldan Ishga Tushirish Ketma-Ketligi

Loyihani GitHub'dan klon qilgandan so'ng quyidagi 5 ta qadamni bajaring:

### 1-qadam: Kutubxonalarni o'rnatish

```powershell
# Python kutubxonalari:
pip install -r telegram_bot/requirements.txt
pip install -r web/requirements.txt

# Frontend kutubxonalari:
cd frontend
npm install
cd ..
```

---

### 2-qadam: `.env` fayllarini sozlash

Yuqorida ko'rsatilganidek, `telegram_bot/.env` va `web/.env.web` fayllarini yaratib, o'zingizning DB va Telegram ma'lumotlaringizni kiriting.

---

### 3-qadam: Ma'lumotlar bazasini tayyorlash

PostgreSQL ishlab turganiga ishonch hosil qiling va loyiha ildizida quyidagi buyruqni bering:
```powershell
python apply_schema.py
```
*Bu skript `face_id_terminal` bazasini tekshiradi, barcha jadvallarni yaratadi va standart admin (`admin` / `admin123`) akkauntini kiritadi.*

---

### 4-qadam: Telegram Bot va Webhook tinglovchisini ishga tushirish

1-terminalda:
```powershell
cd telegram_bot
python main.py
```
*Kutilayotgan natija:*
```text
INFO 🤖 Bot va server ishga tushdi...
INFO Serving on http://0.0.0.0:8095
```

---

### 5-qadam: Web Backend va Frontendni ishga tushirish

2-terminalda (Backend API):
```powershell
cd web
uvicorn app.main:app --host 127.0.0.1 --port 8090 --reload
```
*Interaktiv API hujjatlari (Swagger): `http://127.0.0.1:8090/docs`*

3-terminalda (Frontend Dashboard):
```powershell
cd frontend
npm run dev
```
*Brauzerda boshqaruv paneli:* **`http://localhost:3005`**

---

## 🔐 Standart Kirish Ma'lumotlari

- **Panel manzili:** `http://localhost:3005`
- **Login:** `admin`
- **Parol:** `admin123`

*(Tizimga kirgach, «Sozlamalar» ➡️ «Adminlar va Rollar» bo'limida yangi adminlar qo'shishingiz yoki parolni yangilashingiz mumkin).*

---

## 📹 Hikvision Face ID Terminalini Sozlash

Terminal yuzni aniqlaganida botga xabar yuborishi uchun terminal web-interfeysida quyidagicha sozlanadi:
1. Brauzerda Hikvision terminal IP manziliga kiring (masalan: `http://192.168.11.151`).
2. **Configuration** ➡️ **Network** ➡️ **Advanced Settings** ➡️ **HTTP Listening** (yoki **Surveillance Center**):
   - **Destination IP:** Bot ishlayotgan kompyuter/server IP manzili (masalan: `192.168.11.100`)
   - **Port:** `8095`
   - **URL:** `/`
   - **Protocol:** `HTTP`
3. Sozlamani saqlang. Endi har safar xodim terminaldan o'tganida, terminal botga avtomatik POST so'rov yuboradi.
