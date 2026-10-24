-- ========================================================
-- Davomat Tizimi: PostgreSQL Ma'lumotlar Bazasi Sxemasi
-- Versiya: 1.0 (Test va Production uchun)
-- ========================================================

-- 1. Mavjud jadvallarni yaratish va kengaytirish
CREATE TABLE IF NOT EXISTS attendance (
    id SERIAL PRIMARY KEY,
    emp_no TEXT,
    employee_name TEXT,
    event_type TEXT,          -- 'checkIn' | 'checkOut'
    event_time TIMESTAMP,     -- Toshkent vaqti, tz'siz
    late_minutes INT DEFAULT 0,
    serial_no BIGINT          -- Qurilma serial raqami
);
CREATE INDEX IF NOT EXISTS idx_att_time ON attendance(event_time);
CREATE INDEX IF NOT EXISTS idx_att_emp_time ON attendance(emp_no, event_time);

CREATE TABLE IF NOT EXISTS employees (
    emp_no TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    work_start TIME NOT NULL DEFAULT '09:00:00',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    department TEXT,
    job_title TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS admins (
    tg_id BIGINT PRIMARY KEY,
    name TEXT,
    role TEXT NOT NULL DEFAULT 'admin',  -- 'admin' | 'viewer'
    username TEXT UNIQUE,
    password_hash TEXT
);

CREATE TABLE IF NOT EXISTS chats (
    chat_id BIGINT PRIMARY KEY,
    title TEXT
);

-- 2. Kesh va versiya sinxronizatsiyasi
CREATE TABLE IF NOT EXISTS config_version (
    id INT PRIMARY KEY DEFAULT 1 CHECK (id=1),
    version BIGINT NOT NULL DEFAULT 1
);
INSERT INTO config_version (id, version) VALUES (1, 1) ON CONFLICT (id) DO NOTHING;

-- 3. Kunlik yig'ma jadval (Dashboard va tezkor hisobotlar uchun)
CREATE TABLE IF NOT EXISTS daily_attendance (
    emp_no TEXT NOT NULL REFERENCES employees(emp_no) ON DELETE CASCADE,
    day DATE NOT NULL,
    first_in TIMESTAMP,
    last_out TIMESTAMP,
    late_minutes INT NOT NULL DEFAULT 0,
    worked_minutes INT,
    events_count INT NOT NULL DEFAULT 0,
    status TEXT NOT NULL,   -- present | late | absent | leave | weekend | holiday
    PRIMARY KEY (emp_no, day)
);
CREATE INDEX IF NOT EXISTS idx_daily_att_day ON daily_attendance (day);
CREATE INDEX IF NOT EXISTS idx_daily_att_status ON daily_attendance (status);

-- 4. Qo'lda kiritilgan tuzatishlar (Xom attendance o'zgarmaydi)
CREATE TABLE IF NOT EXISTS attendance_adjustments (
    id BIGSERIAL PRIMARY KEY,
    emp_no TEXT NOT NULL REFERENCES employees(emp_no) ON DELETE CASCADE,
    day DATE NOT NULL,
    status_override TEXT,     -- present | late | absent | leave | weekend | holiday
    new_first_in TIME,
    reason TEXT,
    fine_amount NUMERIC(12,2) DEFAULT 0,
    created_by BIGINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (emp_no, day)
);

-- 5. Ish va dam olish kalendari
CREATE TABLE IF NOT EXISTS calendar_days (
    day DATE PRIMARY KEY,
    is_workday BOOLEAN NOT NULL,
    note TEXT
);

-- 6. Tizim sozlamalari (JSON formatida)
CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value JSONB NOT NULL
);

-- Boshlang'ich sozlamalar
INSERT INTO app_settings (key, value) VALUES
('general', '{"work_start": "09:00", "grace_minutes": 0, "retention_days": 180, "weekend_days": [6]}'),
('telegram', '{"notify_absent_time": "09:30", "send_absent_group": false}')
ON CONFLICT (key) DO NOTHING;

-- 7. Audit jurnali (O'zgarishlar tarixi)
CREATE TABLE IF NOT EXISTS audit_log (
    id BIGSERIAL PRIMARY KEY,
    at TIMESTAMPTZ NOT NULL DEFAULT now(),
    actor BIGINT,
    action TEXT NOT NULL,
    target TEXT,
    details JSONB
);
CREATE INDEX IF NOT EXISTS idx_audit_at ON audit_log (at DESC);

-- 8. Standart admin foydalanuvchisi (Agar ro'yxat bo'sh bo'lsa)
-- Login: admin, Parol: admin123 (Argon2 hash)
INSERT INTO admins (tg_id, name, role, username, password_hash)
VALUES (
    1,
    'Tizim Administratori',
    'admin',
    'admin',
    '$argon2id$v=19$m=65536,t=3,p=4$UcqZ856TUkrJeQ9hbK0VQg$oW3aSn7Au39ZPuhpLDwHjfSAdPpBgz8YD7nDCN2f5BQ'
) ON CONFLICT (tg_id) DO UPDATE SET password_hash = EXCLUDED.password_hash;
