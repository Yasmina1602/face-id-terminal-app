"""Initial schema expansion and new tables for web app

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-24 11:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Mavjud jadvallarni xavfsiz kengaytirish
    op.execute("ALTER TABLE employees ADD COLUMN IF NOT EXISTS department TEXT;")
    op.execute("ALTER TABLE employees ADD COLUMN IF NOT EXISTS job_title TEXT;")
    op.execute("ALTER TABLE employees ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();")
    
    op.execute("ALTER TABLE admins ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'admin';")
    op.execute("ALTER TABLE admins ADD COLUMN IF NOT EXISTS username TEXT UNIQUE;")
    op.execute("ALTER TABLE admins ADD COLUMN IF NOT EXISTS password_hash TEXT;")
    
    op.execute("ALTER TABLE attendance ADD COLUMN IF NOT EXISTS serial_no BIGINT;")

    # 2. Yangi jadvallar
    op.execute("""
        CREATE TABLE IF NOT EXISTS config_version (
            id INT PRIMARY KEY DEFAULT 1 CHECK (id=1),
            version BIGINT NOT NULL DEFAULT 1
        );
        INSERT INTO config_version (id, version) VALUES (1, 1) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS daily_attendance (
            emp_no TEXT NOT NULL REFERENCES employees(emp_no) ON DELETE CASCADE,
            day DATE NOT NULL,
            first_in TIMESTAMP,
            last_out TIMESTAMP,
            late_minutes INT NOT NULL DEFAULT 0,
            worked_minutes INT,
            events_count INT NOT NULL DEFAULT 0,
            status TEXT NOT NULL,
            PRIMARY KEY (emp_no, day)
        );
        CREATE INDEX IF NOT EXISTS idx_daily_att_day ON daily_attendance (day);
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS attendance_adjustments (
            id BIGSERIAL PRIMARY KEY,
            emp_no TEXT NOT NULL REFERENCES employees(emp_no) ON DELETE CASCADE,
            day DATE NOT NULL,
            status_override TEXT,
            new_first_in TIME,
            reason TEXT,
            fine_amount NUMERIC(12,2) DEFAULT 0,
            created_by BIGINT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (emp_no, day)
        );
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS calendar_days (
            day DATE PRIMARY KEY,
            is_workday BOOLEAN NOT NULL,
            note TEXT
        );
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value JSONB NOT NULL
        );
        INSERT INTO app_settings (key, value) VALUES
        ('general', '{"work_start": "09:00", "grace_minutes": 0, "retention_days": 180, "weekend_days": [6]}')
        ON CONFLICT (key) DO NOTHING;
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id BIGSERIAL PRIMARY KEY,
            at TIMESTAMPTZ NOT NULL DEFAULT now(),
            actor BIGINT,
            action TEXT NOT NULL,
            target TEXT,
            details JSONB
        );
        CREATE INDEX IF NOT EXISTS idx_audit_at ON audit_log (at DESC);
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS audit_log CASCADE;")
    op.execute("DROP TABLE IF EXISTS app_settings CASCADE;")
    op.execute("DROP TABLE IF EXISTS calendar_days CASCADE;")
    op.execute("DROP TABLE IF EXISTS attendance_adjustments CASCADE;")
    op.execute("DROP TABLE IF EXISTS daily_attendance CASCADE;")
    op.execute("DROP TABLE IF EXISTS config_version CASCADE;")
