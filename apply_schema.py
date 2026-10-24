import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Windows console encoding fix
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Avval telegram_bot/.env dan, so'ngra web/.env.web dan o'qiymiz
tb_env = os.path.join(os.path.dirname(__file__), "telegram_bot", ".env")
web_env = os.path.join(os.path.dirname(__file__), "web", ".env.web")

if os.path.exists(tb_env):
    load_dotenv(tb_env)
if os.path.exists(web_env):
    load_dotenv(web_env)

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "face_id_terminal")
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "1234")

print(f"[*] PostgreSQL ulanish tekshirilmoqda: {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

# 1. Baza mavjudligini tekshirish, bo'lmasa yaratish
try:
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, database="postgres"
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
    exists = cur.fetchone()
    if not exists:
        print(f"[+] '{DB_NAME}' ma'lumotlar bazasi topilmadi. Avtomatik yaratilmoqda...")
        cur.execute(f'CREATE DATABASE "{DB_NAME}"')
        print(f"[OK] '{DB_NAME}' bazasi yaratildi!")
    else:
        print(f"[OK] '{DB_NAME}' bazasi mavjud.")
    cur.close()
    conn.close()
except Exception as e:
    print(f"[!] Ogohlantirish (postgres bazasiga ulanish): {e}")

# 2. schema.sql faylini bajarish
schema_file = os.path.join(os.path.dirname(__file__), "schema.sql")
if not os.path.exists(schema_file):
    print(f"[X] Xato: {schema_file} topilmadi!")
    exit(1)

with open(schema_file, "r", encoding="utf-8") as f:
    sql_script = f.read()

try:
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, database=DB_NAME
    )
    cur = conn.cursor()
    cur.execute(sql_script)
    conn.commit()
    cur.close()
    conn.close()
    print("[OK] schema.sql muvaffaqiyatli bajarildi!")
    print("[OK] Barcha jadvallar va standart admin yaratildi (Login: admin / Parol: admin123).")
except Exception as e:
    print(f"[X] Bazaga schema.sql yuklashda xatolik: {e}")
    exit(1)
