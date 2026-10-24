# Davomat tizimi: Web ilova qo'shish uchun master prompt

Versiya 1.0 | 2026-10-24 | Hikvision + Telegram bot + PostgreSQL + yangi Web dashboard

Bu hujjat to'liq prompt: uni AI yordamchiga (yoki dasturchiga) boshidan oxirigacha bering. Hujjatda mavjud tizim, maqsad, arxitektura, baza (MBBT), bot bilan bog'lanish, server, xavfsizlik, bosqichlar va qabul mezonlari bor.

## 1. Rol va vazifa

Sen senior full-stack muhandissan (Python, PostgreSQL, TypeScript/React, Linux). Mavjud davomat tizimiga **alohida web ilova** qo'shasan: statistika dashboardi, xodim va admin boshqaruvi, hisobotlar va qo'shimcha funksiyalar.

Qoidalar:

- Mavjud botning ishlashini buzma. Bot qurilmadan keladigan eventlarni qabul qilishda kritik yo'l hisoblanadi.
- Server bitta va kuchsiz: har bir qaror yengillikni hisobga olsin.
- Har bosqichda: fayllar daraxti, to'liq kod, ishga tushirish buyruqlari, testlar va qabul tekshiruvini ber.
- Taxmin qilishga to'g'ri kelsa, taxminni ro'yxat qilib yoz. Faqat to'sib qo'yadigan savollarni ber.
- Kod sharhlari va foydalanuvchi interfeysi o'zbek tilida (lotin), o'zgaruvchi nomlari inglizcha.

## 2. Mavjud tizim (o'zgartirilmaydi, faqat kengaytiriladi)

**Oqim:** Hikvision yuz tanish terminali (IP 192.168.11.151) har o'tishda botga HTTP POST yuboradi (multipart: `AccessControllerEvent` JSON maydoni va `Picture` fayli). Bot portni `PORT` (8095) da tinglaydi.

**Qurilma eventlari:**

- `subEventType 75` haqiqiy o'tish: `employeeNoString`, `name`, `attendanceStatus` (`checkIn`/`checkOut`), `label` (`Keldim`/`Ketdim`), rasm bor.
- `subEventType 21/22` eshik qulfi hodisalari, e'tiborsiz qoldiriladi.
- Qurilma vaqti `+05:00` bilan keladi (soati NTP bilan to'g'rilanishi shart).

**Bot (`main.py`, Python 3.12):** Flask + waitress (2 thread), python-telegram-bot v21+ (polling), psycopg2 `ThreadedConnectionPool(1,3)`, `requests`, `openpyxl`. Mantiq:

- Faqat ro'yxatdagi (`employees`, `active=true`) xodimlarning Keldim/Ketdim eventlari qabul qilinadi, rasmsiz event tashlanadi, 30 soniya ichidagi takror tashlanadi.
- Kechikish: kunning **birinchi** `checkIn` vaqti > `work_start + GRACE_MINUTES` bo'lsa, `late_minutes` = start dan boshlab daqiqa (kamida 1). Keyingi kirishlar `late=0`.
- Rasm Telegramga navbat (`queue`, 50) orqali bitta fon oqimida yuboriladi (TELEGRAM\_CHAT\_ID, ro'yxatdagi guruhlar, yo'q bo'lsa adminlar). Rasm bazada **saqlanmaydi**.
- Xodimlar, adminlar, guruhlar **xotira keshida** (`EMP`, `ADMINS`, `CHATS`), ishga tushganda va admin amallarida yangilanadi.
- Admin paneli Telegramda: bugungi/haftalik hisobot, Excel (bitta xodim / barcha xodimlar), xodim qo'shish, ish vaqtini o'zgartirish, admin qo'shish/o'chirish.
- `RETENTION_DAYS` (180) dan eski `attendance` yozuvlari har kecha 03:00 da o'chiriladi.
- Vaqt: `event_time` **tz'siz** TIMESTAMP, Toshkent (Asia/Tashkent) mahalliy vaqti.

**Mavjud jadvallar (bot yaratadi, struktura buzilmasin):**

```sql
attendance(id serial pk, emp_no text, employee_name text,
           event_type text,        -- 'checkIn' | 'checkOut'
           event_time timestamp,   -- Toshkent vaqti, tz'siz
           late_minutes int default 0)
-- indekslar: (event_time), (emp_no, event_time)
employees(emp_no text pk, name text not null, work_start time not null, active bool default true)
admins(tg_id bigint pk, name text)
chats(chat_id bigint pk, title text)
```

**Infratuzilma:** Ubuntu 24 server, loyiha `~/ser`, Python venv, bot `systemd` xizmati `davomat-bot`, PostgreSQL 16 Docker konteynerida (`davomat-db`, faqat `127.0.0.1:5433`, baza `attand`). Eslatma: 8080-portni boshqa `uvicorn` ishlatadi. Yangi portlarni `ss -ltnp` bilan tekshir.

## 3. Maqsad va funksiyalar

**Dashboard (asosiy sahifa), tez ochiladi, har 60 soniyada yangilanadi:**

- KPI kartalar: bugun kelganlar, kelmaganlar, kech qolganlar, vaqtida kelish foizi.
- Jonli lenta: oxirgi 20 o'tish (ism, vaqt, kechikish).
- Trend: oxirgi 30/90 kunda kechikish foizi va o'rtacha kelish vaqti.
- Reyting: eng ko'p kechikkan 10 xodim, eng intizomli 10 xodim.
- Taqsimot: kelish vaqti gistogrammasi, hafta kuni x soat issiqlik xaritasi.
- Bo'limlar kesimi (agar `department` to'ldirilgan bo'lsa).

**Boshqaruv:**

- Xodimlar: ro'yxat, qidiruv, qo'shish, tahrirlash (ism, ish boshlanishi, bo'lim, lavozim), faolsizlantirish.
- Xodim profili: oylik kalendar (rangli kunlar), statistika, o'tishlar tarixi.
- Adminlar va rollar: `admin` (hammasi), `viewer` (faqat ko'rish).
- Telegram guruhlari ro'yxati, guruhni uzish.
- Davomat jadvali: filtrlar (sana, xodim, holat), qo'lda tuzatish (holat, sabab, kelgan vaqti, jarima) **tuzatish jadvali orqali**, xom `attendance` o'zgarmaydi.
- Hisobotlar: Excel (bitta xodim / barcha xodimlar), davr tanlash.
- Sozlamalar: standart ish boshlanishi, imtiyoz daqiqasi, dam olish kunlari, bayram kalendari, xabar vaqtlari.
- Audit jurnali: kim, nima, qachon o'zgartirdi.
- Bildirishnoma: ish kuni 09:30 da "kelmaganlar" ro'yxati Telegram guruhiga (ixtiyoriy).

## 4. Arxitektura

```
Hikvision --(8095, faqat qurilma IP)--> BOT (Python, mavjud)
Telegram  <----------------------------+     |
                                             v
Brauzer --443--> Caddy --/api--> WEB API (FastAPI) --> PostgreSQL (127.0.0.1:5433)
                   |                  |   ^                    ^
                   +--statik fayllar  |   +-- job: yig'ish ----+
                      (React dist)    +-- job: CRM push (ixtiyoriy)
```

Prinsiplar:

1. **Alohida jarayonlar:** bot va web bir-biriga import qilmaydi. Faqat umumiy baza orqali ishlaydi.
2. **Bot yo'li o'zgarmaydi:** web ishdan chiqsa ham, qurilma eventlari yoziladi va Telegramga ketadi.
3. **Yig'ma jadval:** dashboard xom `attendance` dan emas, `daily_attendance` dan o'qiydi.
4. **Xom ma'lumot o'zgarmas:** qo'lda tuzatishlar alohida jadvalda, yakuniy holat ikkalasini birlashtiradi.
5. **Bitta manba:** xodimlar, adminlar, sozlamalar bazada. Ikkala tomon ham shundan o'qiydi.

## 5. Texnologiyalar

- **Backend:** Python 3.12, FastAPI, Uvicorn (1 worker), SQLAlchemy 2.0 yoki `psycopg` 3 (pool max 3), Alembic (faqat yangi jadvallar uchun), Pydantic v2, `openpyxl` (Excel), APScheduler (job'lar, web ichida).
- **Frontend:** React + Vite + TypeScript, Tailwind, TanStack Query (`refetchInterval` 60 s), ECharts yoki Recharts. Build natijasi (`dist`) statik fayl, Node jarayoni ishlamaydi.
- **Proksi:** Caddy (avtomatik HTTPS, gzip/zstd).
- **Kirish:** Telegram Login Widget (asosiy), zaxira: login + parol (argon2). Sessiya: `HttpOnly`, `Secure`, `SameSite=Lax` cookie.
- **Test/sifat:** pytest, httpx TestClient, ruff, mypy (backend), ESLint (frontend).

## 6. Ma'lumotlar bazasi (MBBT) qismi

**6.1. Mavjud jadvallarga qo'shimcha (orqaga mos, bot uchun xavfsiz):**

```sql
ALTER TABLE employees ADD COLUMN IF NOT EXISTS department text;
ALTER TABLE employees ADD COLUMN IF NOT EXISTS job_title  text;
ALTER TABLE employees ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();
ALTER TABLE admins    ADD COLUMN IF NOT EXISTS role text NOT NULL DEFAULT 'admin';
ALTER TABLE attendance ADD COLUMN IF NOT EXISTS serial_no bigint;  -- qurilmaning serialNo (CRM event_id uchun)
```

**6.2. Yangi jadvallar (web egalik qiladi, Alembic orqali):**

```sql
CREATE TABLE config_version (id int PRIMARY KEY DEFAULT 1 CHECK (id=1), version bigint NOT NULL DEFAULT 1);
INSERT INTO config_version DEFAULT VALUES ON CONFLICT DO NOTHING;

CREATE TABLE daily_attendance (
  emp_no text NOT NULL, day date NOT NULL,
  first_in timestamp, last_out timestamp,
  late_minutes int NOT NULL DEFAULT 0, worked_minutes int,
  events_count int NOT NULL DEFAULT 0,
  status text NOT NULL,   -- present | late | absent | leave | weekend | holiday
  PRIMARY KEY (emp_no, day));
CREATE INDEX ON daily_attendance (day);

CREATE TABLE attendance_adjustments (
  id bigserial PRIMARY KEY, emp_no text NOT NULL, day date NOT NULL,
  status_override text, new_first_in time, reason text, fine_amount numeric(12,2),
  created_by bigint, created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (emp_no, day));

CREATE TABLE calendar_days (day date PRIMARY KEY, is_workday boolean NOT NULL, note text);
CREATE TABLE app_settings (key text PRIMARY KEY, value jsonb NOT NULL);
CREATE TABLE audit_log (id bigserial PRIMARY KEY, at timestamptz NOT NULL DEFAULT now(),
  actor bigint, action text NOT NULL, target text, details jsonb);
```

**6.3. Yig'ish (aggregator) qoidalari.** `rebuild(day_from, day_to)` idempotent upsert:

- `first_in` = shu kundagi birinchi `checkIn`, `last_out` = oxirgi `checkOut`, `late_minutes` = shu birinchi kirishdagi qiymat, `worked_minutes` = `last_out - first_in` (ikkalasi bor va ketma-ket bo'lsa).
- Status: `late` (late>0), `present`, aks holda ish kuni bo'lsa va kun tugagan bo'lsa `absent`; dam olish/bayram bo'lsa `weekend`/`holiday`. Ish kuni: `calendar_days` yozuvi, bo'lmasa `WEEKEND_DAYS` ga qarab.
- `attendance_adjustments` bor bo'lsa, `status_override` va `new_first_in` yakuniy qiymatni bosadi (kechikish qayta hisoblanadi).
- Jadval: bugun har 5 daqiqada, oxirgi 7 kun har kecha 00:30 da qayta quriladi. Birinchi ishga tushishda mavjud tarix to'liq yig'iladi.
- **Muhim:** botning 180 kunlik tozalashi yig'ishdan oldin eski eventlarni o'chirmasligi kerak (`daily_attendance` allaqachon yig'ilgan bo'lishi sharti).

**6.4. Rollar va huquqlar:**

```sql
CREATE ROLE davomat_web LOGIN PASSWORD '<kuchli>';
GRANT SELECT ON attendance TO davomat_web;                 -- xom eventlarga yozish yo'q
GRANT SELECT, INSERT, UPDATE, DELETE ON employees, admins, chats, daily_attendance,
      attendance_adjustments, calendar_days, app_settings TO davomat_web;
GRANT SELECT, INSERT ON audit_log TO davomat_web;
GRANT SELECT, UPDATE ON config_version TO davomat_web;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO davomat_web;
```

Bot hozirgi foydalanuvchi bilan ishlashda davom etadi. Bazaga tashqaridan ulanish yo'q (`127.0.0.1`).

**6.5. Zaxira:** har kecha `docker exec davomat-db pg_dump -U <user> attand | gzip > /var/backups/davomat/attand_$(date +%F).sql.gz`, 14 kun saqlanadi. Migratsiyadan oldin qo'lda zaxira shart.

## 7. Bot bilan bog'lanish

Bog'lanish **faqat baza orqali**. Botga kiritiladigan minimal o'zgarishlar:

1. **Kesh sinxronlash.** Bot har 30 soniyada `SELECT version FROM config_version` (juda arzon). Qiymat o'zgargan bo'lsa `load_caches()` chaqiriladi (`job_queue.run_repeating(..., interval=30)`).
2. **Botdagi admin amallari** (xodim/admin/guruh o'zgarishi) ham `UPDATE config_version SET version=version+1` qiladi. Web ham xuddi shunday, o'zgarish ichida.
3. **`serial_no`.** Webhook `inner.get("serialNo")` ni `attendance.serial_no` ga yozadi (CRM `event_id` uchun, ixtiyoriy).
4. **Tozalash tartibi.** Bot `cleanup_old()` faqat `daily_attendance` yig'ilgan kunlargacha o'chiradi.
5. Yangi ustunlarni (`department`, `role` va h.k.) bot e'tiborsiz qoldiradi, ishlashi buzilmaydi.

Web ilovadan Telegramga xabar yuborish (kelmaganlar ro'yxati) kerak bo'lsa: web **faqat `sendMessage`** ni to'g'ridan-to'g'ri Bot API orqali chaqiradi. `getUpdates` ni hech qachon chaqirmaydi (aks holda botda `Conflict` xatosi chiqadi).

**Rasm:** hozir saqlanmaydi (server yukini kamaytirish uchun). Dashboardda rasm kerak bo'lsa, faqat ixtiyoriy rejim: bot kichraytirilgan JPEG (<=30 KB) ni diskka yozadi, `attendance.photo_path`, 30 kun saqlanadi. Standart holatda **o'chiq**.

## 8. Web API (FastAPI, prefiks `/api`)

Umumiy: JSON, vaqtlar ISO 8601 `+05:00` bilan, sahifalash `page`/`limit` (<=100), xato formati `{"error":{"code","message"}}`, barcha so'rovlar sessiyani va rolni tekshiradi.

| Metod | Yo'l | Rol | Tavsif |
| --- | --- | --- | --- |
| POST | `/auth/telegram` | - | Login Widget ma'lumotini tekshirish (HMAC-SHA256, `auth_date` <= 24 soat), `admins` da bo'lsa cookie beradi |
| POST | `/auth/logout`, GET `/auth/me` | har kim | Chiqish, joriy foydalanuvchi |
| GET | `/stats/overview` | viewer+ | Bugungi KPI |
| GET | `/stats/trend?days=30` | viewer+ | Kunlik kechikish foizi, o'rtacha kelish |
| GET | `/stats/ranking?from&to` | viewer+ | Eng ko'p kechikkan / intizomli |
| GET | `/stats/arrival-hist`, `/stats/heatmap` | viewer+ | Taqsimotlar |
| GET | `/events/recent?limit=20` | viewer+ | Jonli lenta |
| GET/POST/PATCH | `/employees`, `/employees/{emp_no}` | admin (GET: viewer) | Xodimlar CRUD, faolsizlantirish (o'chirish emas) |
| GET | `/employees/{emp_no}/calendar?month=2026-10` | viewer+ | Oylik kunlar |
| GET | `/attendance?from&to&emp_no&status` | viewer+ | Kunlik jadval (`daily_attendance` + tuzatishlar) |
| PUT | `/attendance/{emp_no}/{day}/adjustment` | admin | Qo'lda tuzatish (audit yoziladi) |
| GET | `/reports/employee/{emp_no}/export?from&to` | viewer+ | Excel, bitta xodim |
| GET | `/reports/summary/export?from&to` | viewer+ | Excel, barcha xodimlar |
| GET/POST/DELETE | `/admins` | admin | Adminlar va rollar |
| GET/DELETE | `/chats` | admin | Telegram guruhlari |
| GET/PUT | `/settings`, `/calendar` | admin | Sozlamalar, bayramlar |
| GET | `/audit?page` | admin | Audit jurnali |
| GET | `/health` | - | Baza va job holati |

Excel tuzilishi bot hisobotlari bilan bir xil: **bitta xodim** varag'ida har kun (sana, hafta kuni, holat, kelgan, ketgan, ish vaqti, kechikish, sabab, jarima, JAMI qatori); **barcha xodimlar** faylida "Umumiy", "Kunlik" va "Tabel" (xodim x kun) varaqlari. Davr <= 366 kun, bir vaqtda bitta eksport (semafor), `write_only` rejimi.

## 9. Server va joylashtirish (bitta Ubuntu server)

Qaror: **hammasi systemd + Caddy**, faqat PostgreSQL Docker'da qoladi (u `127.0.0.1:5433` ga bog'langani uchun boshqa konteynerdan ko'rinmaydi, shuning uchun web ham konteynersiz).

```
~/ser/
  bot/main.py, .env, venv/        # mavjud
  web/app/ (FastAPI), alembic/, .env.web, venv/
  web/frontend/ -> build -> web/dist/
  deploy/Caddyfile, davomat-web.service, backup.sh
```

`davomat-web.service`:

```ini
[Service]
WorkingDirectory=/home/norahara/ser/web
ExecStart=/home/norahara/ser/web/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8090 --workers 1
EnvironmentFile=/home/norahara/ser/web/.env.web
Restart=always
User=norahara
MemoryMax=250M
CPUQuota=50%
Nice=10
```

(8090 band bo'lsa boshqa port tanlang.)

`Caddyfile`:

```
davomat.example.uz {
  encode zstd gzip
  handle /api/* { reverse_proxy 127.0.0.1:8090 }
  handle {
    root * /home/norahara/ser/web/dist
    try_files {path} /index.html
    file_server
  }
}
```

**Tarmoq:**

- 80/443: ochiq (Caddy). SSH: sizga kerakli manzildan.
- 8095 (bot webhook): faqat qurilma: `ufw allow from 192.168.11.151 to any port 8095 proto tcp`.
- 8090 va 5433: faqat `127.0.0.1`, tashqariga yopiq.
- Telegram Login uchun: BotFather `/setdomain` ga domen yoziladi (HTTPS shart).

**Resurs byudjeti (taxminiy):** PostgreSQL 256 MB, bot \~100 MB, web \~150 MB, Caddy \~30 MB. Loglar `journald` (`SystemMaxUse=200M`), Docker `json-file` (`max-size=10m`, `max-file=3`).

## 10. Yengillik qoidalari

- Dashboard faqat `daily_attendance` va oxirgi kunlar uchun kichik so'rovlar bilan ishlaydi. Katta davrda xom `attendance` ga murojaat yo'q.
- Overview va ranking natijalari xotirada 30-60 soniya keshlanadi.
- Frontend polling >= 60 soniya, sahifa yashirin (fonda) bo'lsa to'xtaydi.
- DB pool max 3, so'rov `statement_timeout` 5 s, sahifalash majburiy.
- Excel: semafor 1, `write_only`, davr limiti. Katta fayl uzoq cho'zilsa, fon vazifasi va yuklash havolasi.
- Har yangi so'rov uchun `EXPLAIN` bilan indeks ishlatilishi tekshiriladi.
- Bot kodida `LOG_LEVEL=INFO`, web'da so'rov loglari faqat xatolar.

## 11. Xavfsizlik

- Sirlar (`.env*`) `chmod 600`, git'ga kirmaydi. Parollar kodda yo'q.
- Telegram `hash` va `auth_date` tekshiruvi, sessiya muddati cheklangan (masalan 12 soat), `SameSite=Lax` + `Origin` tekshiruvi (CSRF).
- Rate limit: login va eksport endpointlarida.
- Pydantic bilan barcha kirishlar validatsiya qilinadi, SQL faqat parametrli.
- Rol tekshiruvi har endpointda, `viewer` faqat o'qiydi.
- Har o'zgartirish `audit_log` ga yoziladi.
- Shaxsiy ma'lumot minimal: faqat ism, ID, vaqt. Rasm standart holatda saqlanmaydi.

## 12. Ishlash bosqichlari va qabul mezonlari

**F0. Tayyorgarlik.** Zaxira (`pg_dump`), bot kodining git'ga olinishi, staging nusxa. *Mezon:* zaxira tiklab sinab ko'rilgan.

**F1. Baza va bot tayyorgarligi.** Alembic migratsiyalari (6.1, 6.2), `davomat_web` roli, botga kesh sinxronlash va `serial_no`. *Mezon:* botdan tashqarida `config_version` oshirilganda bot 30 soniyada yangi xodimni ko'radi; qurilmadan o'tish avvalgidek ishlaydi.

**F2. Backend.** Auth, xodim/admin/sozlama API, aggregator va statistika endpointlari. *Mezon:* barcha endpointlar uchun testlar o'tadi; `daily_attendance` bot hisoblagan kechikish bilan mos keladi; overview < 200 ms.

**F3. Frontend.** Dashboard, xodimlar, davomat jadvali, profil kalendari. *Mezon:* mobil va kompyuterda ishlaydi, chiqish/kirish oqimi to'liq, rolga qarab tugmalar yashiriladi.

**F4. Hisobot, tuzatish, audit.** Excel eksport, qo'lda tuzatish, audit jurnali, bildirishnomalar. *Mezon:* Excel fayllari botdagi bilan bir xil raqam beradi; tuzatish xom `attendance` ni o'zgartirmaydi.

**F5. Joylashtirish va xavfsizlik.** Caddy + HTTPS, `ufw` qoidalari, systemd, zaxira cron, monitoring (`/health`). *Mezon:* 8090 va 5433 tashqaridan ko'rinmaydi, sertifikat avtomatik yangilanadi, web to'xtatilsa bot ishlashda davom etadi.

**F6. Ixtiyoriy.** CRM'ga push, rasm saqlash, ta'til/kasallik modullari.

## 13. CRM integratsiyasi (F6, ixtiyoriy)

Push ishchisi **web servisda** ishlaydi (botga tegilmaydi): `attendance` dagi yangi qatorlarni (`id` > oxirgi yuborilgan, `app_settings` da saqlanadi) CRM'ga yuboradi.

`POST {CRM_URL}/api/attendance/events`, `Authorization: Bearer <CRM_TOKEN>`:

```json
{"event_id":"davomat-1234","employee_no":"00000001","employee_name":"...",
 "type":"check_in","occurred_at":"2026-10-23T06:53:55+05:00",
 "late_minutes":0,"first_check_in_of_day":true}
```

- Javoblar: 201 saqlandi, 200 takror, 401 token xato, 404/422 xodim topilmadi (qayta urinma, ogohlantir), 5xx/timeout qayta urin (eksponensial kechikish).
- CRM `event_id` bo'yicha takrorlanmas (idempotent) bo'lishi shart, javobi <= 2 s.
- Xodimlarni CRM'dan olish: `GET /api/employees?updated_since=` (har 10 daqiqada), `employee_no` qurilma ID bilan mos.

## 14. Kod tashkiloti va sifat

- `web/app`: `api/` (routerlar), `services/` (stats, aggregator, reports), `db/` (modellar, sessiya), `core/` (config, security), `jobs/`.
- Biznes mantiq (kechikish, status) alohida funksiyalarda, birlik testlar bilan (chegaraviy holatlar: 09:00:30, imtiyoz, yarim tun, dam olish kuni).
- Har loyihada `README`, `.env.example`, `Makefile` (`run`, `test`, `migrate`, `build`).
- Migratsiyalar orqaga qaytariladigan (`downgrade`) va mavjud jadvallarni buzmaydi.

## 15. Natija formati (har bosqichda)

1. Qisqa reja va taxminlar ro'yxati.
2. Fayllar daraxti va **to'liq** kod (parchalar emas).
3. Ishga tushirish va tekshirish buyruqlari (aniq terminal komandalari).
4. Testlar va qabul mezonlari bo'yicha natija.
5. Keyingi bosqich va ochiq savollar.

## 16. Boshlashdan oldin tasdiqlanadigan savollar

Standart qiymatlar qavsda, javob bo'lmasa shularni qo'lla:

1. Domen nomi? (bo'lmasa vaqtincha IP + o'zi imzolagan sertifikat, Telegram Login ishlamaydi, login+parol ishlatiladi)
2. Kim ko'radi? (`admin` va `viewer` rollari)
3. Bo'limlar (department) kerakmi? (yo'q, maydon ixtiyoriy)
4. Dam olish kunlari? (faqat yakshanba)
5. Rasmlar dashboardda kerakmi? (yo'q)
6. CRM'ga push kerakmi, qachon? (F6, keyinroq)
7. Davomat tarixi qancha saqlansin? (`daily_attendance` cheksiz, xom `attendance` 180 kun)
