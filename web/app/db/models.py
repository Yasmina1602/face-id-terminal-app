from datetime import datetime, date, time
from sqlalchemy import (
    Column, Integer, BigInteger, String, Boolean, Time,
    Date, DateTime, Numeric, JSON, PrimaryKeyConstraint,
    ForeignKey, text
)
from sqlalchemy.orm import relationship
from app.db.session import Base


class Employee(Base):
    __tablename__ = "employees"

    emp_no = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    work_start = Column(Time, nullable=False, default=time(9, 0))
    active = Column(Boolean, nullable=False, default=True)
    department = Column(String, nullable=True)
    job_title = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)

    daily_records = relationship("DailyAttendance", back_populates="employee", cascade="all, delete-orphan")
    adjustments = relationship("AttendanceAdjustment", back_populates="employee", cascade="all, delete-orphan")


class Admin(Base):
    __tablename__ = "admins"

    tg_id = Column(BigInteger, primary_key=True)
    name = Column(String, nullable=True)
    role = Column(String, nullable=False, default="admin")  # 'admin' | 'viewer'
    username = Column(String, unique=True, nullable=True)
    password_hash = Column(String, nullable=True)


class Chat(Base):
    __tablename__ = "chats"

    chat_id = Column(BigInteger, primary_key=True)
    title = Column(String, nullable=True)


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    emp_no = Column(String, nullable=True, index=True)
    employee_name = Column(String, nullable=True)
    event_type = Column(String, nullable=True)   # 'checkIn' | 'checkOut'
    event_time = Column(DateTime, nullable=True, index=True)
    late_minutes = Column(Integer, default=0)
    serial_no = Column(BigInteger, nullable=True)


class ConfigVersion(Base):
    __tablename__ = "config_version"

    id = Column(Integer, primary_key=True, default=1)
    version = Column(BigInteger, nullable=False, default=1)


class DailyAttendance(Base):
    __tablename__ = "daily_attendance"

    emp_no = Column(String, ForeignKey("employees.emp_no", ondelete="CASCADE"), nullable=False)
    day = Column(Date, nullable=False, index=True)
    first_in = Column(DateTime, nullable=True)
    last_out = Column(DateTime, nullable=True)
    late_minutes = Column(Integer, nullable=False, default=0)
    worked_minutes = Column(Integer, nullable=True)
    events_count = Column(Integer, nullable=False, default=0)
    status = Column(String, nullable=False, index=True)  # present | late | absent | leave | weekend | holiday

    __table_args__ = (
        PrimaryKeyConstraint("emp_no", "day"),
    )

    employee = relationship("Employee", back_populates="daily_records")


class AttendanceAdjustment(Base):
    __tablename__ = "attendance_adjustments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    emp_no = Column(String, ForeignKey("employees.emp_no", ondelete="CASCADE"), nullable=False)
    day = Column(Date, nullable=False)
    status_override = Column(String, nullable=True)
    new_first_in = Column(Time, nullable=True)
    reason = Column(String, nullable=True)
    fine_amount = Column(Numeric(12, 2), default=0)
    created_by = Column(BigInteger, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)

    from sqlalchemy import UniqueConstraint
    __table_args__ = (
        UniqueConstraint("emp_no", "day", name="uq_adjustment_emp_day"),
    )

    employee = relationship("Employee", back_populates="adjustments")


class CalendarDay(Base):
    __tablename__ = "calendar_days"

    day = Column(Date, primary_key=True)
    is_workday = Column(Boolean, nullable=False)
    note = Column(String, nullable=True)


class AppSetting(Base):
    __tablename__ = "app_settings"

    key = Column(String, primary_key=True)
    value = Column(JSON, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False, index=True)
    actor = Column(BigInteger, nullable=True)
    action = Column(String, nullable=False)
    target = Column(String, nullable=True)
    details = Column(JSON, nullable=True)
