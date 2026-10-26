import threading
from contextlib import contextmanager
import psycopg2
from psycopg2.pool import ThreadedConnectionPool

from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS, log

_pool = None
_pool_lock = threading.Lock()


def get_pool():
    global _pool
    with _pool_lock:
        if _pool is None:
            _pool = ThreadedConnectionPool(
                1, 5,
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASS,
            )
        return _pool


@contextmanager
def db():
    """Tranzaksiyani avtomatik commit / rollback qiluvchi xavfsiz DB konteksti"""
    p = get_pool()
    conn = p.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        p.putconn(conn)


def bump_config_version(cur):
    """Kesh yangilanishi uchun konfiguratsiya versiyasini bittaga oshiradi"""
    cur.execute("""
        INSERT INTO config_version (id, version) VALUES (1, 1)
        ON CONFLICT (id) DO UPDATE SET version = config_version.version + 1
    """)


def init_db():
    """Kerakli jadvallar va indekslarni yaratish (migratsiya)"""
    with db() as c, c.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id SERIAL PRIMARY KEY,
                employee_name TEXT,
                event_type TEXT,
                event_time TIMESTAMP,
                late_minutes INT DEFAULT 0
            )""")
        cur.execute("ALTER TABLE attendance ADD COLUMN IF NOT EXISTS emp_no TEXT")
        cur.execute("ALTER TABLE attendance ADD COLUMN IF NOT EXISTS serial_no BIGINT")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_att_time ON attendance(event_time)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_att_emp_time ON attendance(emp_no, event_time)")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                emp_no TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                work_start TIME NOT NULL,
                active BOOLEAN NOT NULL DEFAULT TRUE
            )""")
        cur.execute("ALTER TABLE employees ADD COLUMN IF NOT EXISTS department TEXT")
        cur.execute("ALTER TABLE employees ADD COLUMN IF NOT EXISTS job_title TEXT")
        cur.execute("ALTER TABLE employees ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now()")

        cur.execute("CREATE TABLE IF NOT EXISTS admins (tg_id BIGINT PRIMARY KEY, name TEXT)")
        cur.execute("ALTER TABLE admins ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'admin'")
        cur.execute("CREATE TABLE IF NOT EXISTS chats (chat_id BIGINT PRIMARY KEY, title TEXT)")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS config_version (
                id INT PRIMARY KEY DEFAULT 1 CHECK (id=1),
                version BIGINT NOT NULL DEFAULT 1
            )""")
        cur.execute("INSERT INTO config_version (id, version) VALUES (1, 1) ON CONFLICT DO NOTHING")
    log.info("Ma'lumotlar bazasi jadvallari muvaffaqiyatli tekshirildi.")
