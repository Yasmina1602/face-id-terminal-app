# Davomat Tizimi: Hikvision Face ID + Telegram Bot + Web Dashboard

Ushbu tizim Hikvision yuz tanish terminallari hodisalarini qabul qilish, ko'p filialli (Multi-Branch) arxitektura asosida ma'lumotlarni izolyatsiya qilish, Telegram orqali jonli bildirishnomalar yuborish, ma'lumotlarni PostgreSQL bazasida jamlash hamda real-vaqt rejimida statistikani zamonaviy Web interfeysida ko'rsatish uchun mo'ljallangan.

---

## 🏛️ Tizim Arxitekturasi

Tizim modulli, mustaqil va ko'p filialli kengayuvchan mikro-servis arxitekturasi asosida qurilgan:

```
[ SHAHAR FILIALI ]                         [ URGUT FILIALI ]
Face ID Terminal 1 (192.168.1.150)         Face ID Terminal 2 (192.168.2.150)
        │                                          │
        ▼ (POST /events/shahar)                    ▼ (POST /events/urgut)
───────────────────────────────────────────────────────────────────────────
                           INTERNET
───────────────────────────────────────────────────────────────────────────
                                │
                                ▼
         [ BULUTLI SERVER (Oq IP: 185.120.50.10) ]
         ┌───────────────────────────────────────┐
         │ UFW Firewall                          │
         │   │                                   │
         │   ▼                                   │
         │ Hikvision Receiver (Port: 8095)       │
         │   │ (JSON + Face Img)                 │
         │   ├──► PostgreSQL Baza (5432)         │
         │   │      (branch_code bo'yicha)       │
         │   └──► Telegram Bot                   │
         │          ├──► Shahar Guruhi           │
         │          ├──► Urgut Guruhi            │
         │          ├──► Shahar Admini (Shaxsiy) │
         │          ├──► Urgut Admini (Shaxsiy)  │
         │          └──► Bosh Direktor (Shaxsiy) │
         │                                       │
         │ FastAPI Backend (Port: 8090)          │
         │ React Frontend (Port: 3005 yoki 8090) │
         └───────────────────────────────────────┘
```

### Arxitektura Prinsiplari:
1. **Toza Modulli Tuzilish (Clean Architecture):** `telegram_bot` dasturi 1 ta fayldan qutqarilib, alohida mantiqiy modullarga (`config`, `database`, `repository`, `cache`, `notifier`, `receiver`, `reports`, `bot/`) bo'lindi.
2. **Multi-Branch (Ko'p Filialli Izolyatsiya):** Bitta bot va bitta veb-sayt ishlaydi, biroq filiallar ma'lumotlari bir-biriga aslo ko'rinmaydi. Shahar o'tishlari Shahar guruhiga va adminiga, Urgut o'tishlari esa Urgut guruhiga va adminiga boradi. Bosh direktor esa barchasini jamlangan holda ko'ra oladi.
3. **Kengayuvchanlik (+1 Filial):** Kelajakda yangi terminal (masalan, Samarqand) qo'shilganda kod o'zgarmaydi. Webhook dinamik tarzda `POST /events/{branch_code}` orqali yangi filialni qabul qilaveradi.
4. **Real-Vaqtda Yangilanish (Zero-Lag):** Terminaldan o'tish sodir bo'lishi bilanoq xom `attendance` va yig'ma `daily_attendance` darhol hisoblanadi. Web dashboard yangi o'tishlarni avtomatik aks ettiradi.
5. **Ofitsial iVMS-4200 Integratsiyasi:** Xodimlarni, ularning yuz rasmlarini bitta markaziy kompyuterdagi iVMS-4200 orqali boshqariladi va Cloud P2P orqali masofaviy terminallarga sinxronlashtiriladi.

---

## 📂 `telegram_bot` Modullar Tuzilishi

```text
telegram_bot/
│
├── config.py             # Barcha sozlamalar (.env), vaqt mintaqasi va yordamchilar
├── database.py           # PostgreSQL connection pool va jadvallarni tekshirish (init_db)
├── cache.py              # Xodimlar, adminlar, guruhlarning tezkor RAM keshi va sinxronizatsiyasi
├── repository.py         # Ma'lumotlar bazasi so'rovlari (CRUD)
├── notifier.py           # Telegramga rasmli xabarlarni jo'natish navbati (Queue + Worker)
├── receiver.py           # Hikvision terminalidan JSON va suratlarni qabul qiluvchi HTTP server
├── reports.py            # Matnli va Excel (.xlsx) hisobotlarini shakllantirish
│
├── bot/                  # Telegram Bot qismi
│   ├── keyboards.py      # Barcha Reply va Inline tugmalar
│   ├── handlers.py       # Bot komandalari, matn, callback va guruh hodisalari
│   └── setup.py          # Telegram Application'ni yig'ish va rejalashtirilgan vazifalar
│
└── main.py               # Asosiy ishga tushiruvchi ixcham kirish nuqtasi (Entrypoint)
```

---

## 🔌 Portlar Ro'yxati

| Servis | Port | Vazifasi |
| :--- | :--- | :--- |
| **PostgreSQL** | `5432` | Asosiy ma'lumotlar bazasi (`face_id_terminal`) |
| **Hikvision Receiver / Bot** | `8095` | Hikvision terminallaridan POST qabul qilish |
| **Web Backend (FastAPI)** | `8090` | REST API, analitika va hisobot xizmati |
| **Frontend (Vite / React)** | `3005` | Veb boshqaruv paneli (Dev server) |

---

## 📁 Konfiguratsiya Fayllari (`.env`)

### 1. Telegram Bot uchun: `telegram_bot/.env`
```powershell
Copy-Item telegram_bot\env.example telegram_bot\.env
```

`telegram_bot/.env` asosiy parametrlari:
```env
TELEGRAM_BOT_TOKEN=8747973146:AAEJVvqSyPXtMBVwW8ncUiZHqfCM7udFZvM
TELEGRAM_CHAT_ID=
ADMIN_IDS=

HIKVISION_IP=192.168.11.151
HIKVISION_USER=admin
HIKVISION_PASSWORD=parol_kiriting

PORT=8095

DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=face_id_terminal
DB_USER=root
DB_PASS=1234

DEFAULT_START=09:00
GRACE_MINUTES=0
RETENTION_DAYS=180
WEEKEND_DAYS=6
TZ_NAME=Asia/Tashkent
LOG_LEVEL=INFO

# Terminaldan kelayotgan JSON ma'lumotlarini konsolda to'liq ko'rish (1 - yoqish, 0 - o'chirish)
DEBUG_EVENTS=1
```

---

### 2. Web Backend uchun: `web/.env.web`
```powershell
Copy-Item web\.env.web.example web\.env.web
```

```env
APP_ENV=development
SECRET_KEY=super-secret-key-change-in-production-davomat-2026
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=720

DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=face_id_terminal
DB_USER=root
DB_PASS=1234
DB_POOL_SIZE=3
DB_MAX_OVERFLOW=2

TELEGRAM_BOT_TOKEN=8747973146:AAEJVvqSyPXtMBVwW8ncUiZHqfCM7udFZvM
TZ_NAME=Asia/Tashkent

WEB_PORT=8090
WEB_HOST=0.0.0.0
```

---

## 🚀 Loyihani Ishga Tushirish Ketma-Ketligi

### 1-qadam: Kutubxonalarni o'rnatish
```powershell
pip install -r telegram_bot/requirements.txt
pip install -r web/requirements.txt

cd frontend
npm install
cd ..
```

### 2-qadam: Ma'lumotlar bazasini tayyorlash
```powershell
python apply_schema.py
```

### 3-qadam: Telegram Bot va Webhook tinglovchisini ishga tushirish (1-terminal)
```powershell
cd telegram_bot
python main.py
```

### 4-qadam: Web Backend API ni ishga tushirish (2-terminal)
```powershell
cd web
uvicorn app.main:app --host 127.0.0.1 --port 8090 --reload
```
*API hujjatlari (Swagger):* `http://127.0.0.1:8090/docs`

### 5-qadam: Web Frontendni ishga tushirish (3-terminal)
```powershell
cd frontend
npm run dev
```
*Veb panel:* **`http://localhost:3005`** (Standart login: `admin` / parol: `admin123`)

---

## 📹 Hikvision Face ID Terminalini Sozlash

Terminal yuzni aniqlaganda serverga ma'lumot uzatishi uchun terminal brauzer interfeysida:
1. `http://<TERMINAL_IP>` manziliga kiring.
2. **Configuration** ➡️ **Network** ➡️ **Advanced Settings** ➡️ **HTTP Listening**:
   - **Destination IP:** Server IP manzili (masalan: `185.120.50.10` yoki lokal `192.168.1.100`)
   - **Port:** `8095`
   - **URL:** `/events/shahar` (yoki `/events/urgut`)
   - **Protocol:** `HTTP`
3. Sozlamani saqlang. Har safar xodim o'tganda terminal avtomatik ravishda JSON va olingan fotosuratni serverga yuboradi.

---

## 🛠️ Oxirgi Yangilanishlar va Tuzatishlar
- **CORS & Credentials:** Backendda brauzerlar talabiga mos ravishda domen va portlar aniq ko'rsatilib, kirishdagi loading xatosi to'liq bartaraf etildi.
- **Statistika va Trendlar:** Backenddagi `get_trend` va `get_arrival_histogram` hisob-kitoblaridagi xatoliklar tuzatilib, Dashboarddagi trend grafigi, xodimlar reytingi va issiqlik xaritasi (Heatmap) to'liq ishga tushirildi.
- **Client Timeout:** Frontend API klientiga tarmoq qotib qolmasligi uchun 10 soniyalik xavfsiz timeout kiritildi.
- **DEBUG_EVENTS:** Terminaldan keladigan JSON voqealarni real-vaqtda konsolda kuzatish imkoniyati qo'shildi.
- **MASTER_PROMPT:** Loyihaning ko'p filialli to'liq texnik topshiriq hujjati `MASTER_PROMPT.md` fayliga joylashtirildi.
