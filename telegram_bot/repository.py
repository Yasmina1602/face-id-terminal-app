from datetime import datetime, date, time, timedelta
from database import db, bump_config_version
from config import log, now_local, RETENTION_DAYS


def fetch_all_employees():
    with db() as c, c.cursor() as cur:
        cur.execute("SELECT emp_no, name, work_start, active FROM employees")
        return {r[0]: {"name": r[1], "start": r[2], "active": r[3]} for r in cur.fetchall()}


def fetch_all_admins():
    with db() as c, c.cursor() as cur:
        cur.execute("SELECT tg_id FROM admins")
        return {r[0] for r in cur.fetchall()}


def fetch_all_chats():
    with db() as c, c.cursor() as cur:
        cur.execute("SELECT chat_id FROM chats")
        return {r[0] for r in cur.fetchall()}


def fetch_config_version():
    with db() as c, c.cursor() as cur:
        cur.execute("SELECT version FROM config_version WHERE id=1")
        row = cur.fetchone()
        return row[0] if row else 1


def fetch_today_checkin_ids(d: date):
    s0 = datetime.combine(d, time.min)
    with db() as c, c.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT emp_no FROM attendance 
            WHERE event_type='checkIn' AND event_time >= %s AND event_time < %s
        """, (s0, s0 + timedelta(days=1)))
        return {r[0] for r in cur.fetchall()}


def upsert_employee(emp_no: str, name: str, start: time):
    with db() as c, c.cursor() as cur:
        cur.execute("""
            INSERT INTO employees (emp_no, name, work_start, active) VALUES (%s,%s,%s,TRUE)
            ON CONFLICT (emp_no) DO UPDATE
            SET name = EXCLUDED.name, work_start = EXCLUDED.work_start, active = TRUE
        """, (emp_no, name, start))
        bump_config_version(cur)


def set_work_start(emp_no: str, start: time):
    with db() as c, c.cursor() as cur:
        cur.execute("UPDATE employees SET work_start=%s WHERE emp_no=%s", (start, emp_no))
        bump_config_version(cur)


def set_active(emp_no: str, active: bool):
    with db() as c, c.cursor() as cur:
        cur.execute("UPDATE employees SET active=%s WHERE emp_no=%s", (active, emp_no))
        bump_config_version(cur)


def add_admin(tg_id: int, name: str):
    with db() as c, c.cursor() as cur:
        cur.execute("""
            INSERT INTO admins (tg_id, name) VALUES (%s,%s)
            ON CONFLICT (tg_id) DO UPDATE SET name=EXCLUDED.name
        """, (tg_id, name))
        bump_config_version(cur)


def remove_admin(tg_id: int):
    with db() as c, c.cursor() as cur:
        cur.execute("DELETE FROM admins WHERE tg_id=%s", (tg_id,))
        bump_config_version(cur)


def list_admins():
    with db() as c, c.cursor() as cur:
        cur.execute("SELECT tg_id, COALESCE(name,'') FROM admins ORDER BY tg_id")
        return cur.fetchall()


def add_chat(chat_id: int, title: str):
    with db() as c, c.cursor() as cur:
        cur.execute("""
            INSERT INTO chats (chat_id, title) VALUES (%s,%s)
            ON CONFLICT (chat_id) DO UPDATE SET title=EXCLUDED.title
        """, (chat_id, title))
        bump_config_version(cur)


def remove_chat(chat_id: int):
    with db() as c, c.cursor() as cur:
        cur.execute("DELETE FROM chats WHERE chat_id=%s", (chat_id,))
        bump_config_version(cur)


def update_daily_realtime(cur, emp_no: str, d: date):
    """Event sodir bo'lishi bilan daily_attendance jadvalini darhol yangilash"""
    try:
        cur.execute("""
            WITH stats AS (
                SELECT 
                    MIN(event_time) FILTER (WHERE event_type = 'checkIn') as f_in,
                    MAX(event_time) FILTER (WHERE event_type = 'checkOut') as l_out,
                    COUNT(*) as ev_cnt,
                    COALESCE((SELECT late_minutes FROM attendance 
                              WHERE emp_no = %s AND event_time::date = %s AND event_type = 'checkIn' 
                              ORDER BY event_time ASC LIMIT 1), 0) as l_min
                FROM attendance
                WHERE emp_no = %s AND event_time::date = %s
            )
            INSERT INTO daily_attendance (emp_no, day, first_in, last_out, late_minutes, worked_minutes, events_count, status)
            SELECT 
                %s, %s, f_in, l_out, l_min,
                CASE WHEN f_in IS NOT NULL AND l_out IS NOT NULL AND l_out > f_in 
                     THEN ROUND(EXTRACT(EPOCH FROM (l_out - f_in)) / 60)
                     ELSE NULL END,
                ev_cnt,
                CASE WHEN f_in IS NOT NULL 
                     THEN (CASE WHEN l_min > 0 THEN 'late' ELSE 'present' END)
                     ELSE 'absent' END
            FROM stats
            ON CONFLICT (emp_no, day) DO UPDATE SET
                first_in = EXCLUDED.first_in,
                last_out = EXCLUDED.last_out,
                late_minutes = EXCLUDED.late_minutes,
                worked_minutes = EXCLUDED.worked_minutes,
                events_count = EXCLUDED.events_count,
                status = CASE 
                    WHEN daily_attendance.status IN ('leave', 'holiday', 'weekend') AND EXCLUDED.first_in IS NULL 
                    THEN daily_attendance.status 
                    ELSE EXCLUDED.status 
                END;
        """, (emp_no, d, emp_no, d, emp_no, d))
    except Exception as e:
        log.warning("Realtime daily update ogohlantirish: %s", e)


def save_event(emp_no: str, name: str, etype: str, t: datetime, late: int, serial_no=None):
    with db() as c, c.cursor() as cur:
        cur.execute("""
            INSERT INTO attendance (emp_no, employee_name, event_type, event_time, late_minutes, serial_no)
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (emp_no, name, etype, t, late, serial_no))
        update_daily_realtime(cur, emp_no, t.date())


def cleanup_old():
    cutoff = now_local() - timedelta(days=RETENTION_DAYS)
    with db() as c, c.cursor() as cur:
        try:
            cur.execute("SELECT to_regclass('daily_attendance')")
            reg = cur.fetchone()
            if reg and reg[0]:
                cur.execute("SELECT MAX(day) FROM daily_attendance")
                max_agg = cur.fetchone()
                if max_agg and max_agg[0]:
                    max_dt = datetime.combine(max_agg[0], time.min)
                    if max_dt < cutoff:
                        cutoff = max_dt
        except Exception as e:
            log.warning("cleanup_old check daily_attendance: %s", e)
        cur.execute("DELETE FROM attendance WHERE event_time < %s", (cutoff,))
        log.info("Eski yozuvlar o'chirildi: %s ta", cur.rowcount)
