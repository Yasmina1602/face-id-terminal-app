from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import require_admin, get_password_hash, get_current_user_payload
from app.db.session import get_db
from app.db.models import Admin, ConfigVersion
from app.services.audit import log_audit

router = APIRouter(prefix="/admins", tags=["Adminlar"], dependencies=[Depends(require_admin)])


class AdminCreate(BaseModel):
    tg_id: int
    name: Optional[str] = None
    role: str = "admin"  # 'admin' | 'viewer'
    username: Optional[str] = None
    password: Optional[str] = None


class AdminUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    password: Optional[str] = None


def bump_version(db: Session):
    ver = db.query(ConfigVersion).filter(ConfigVersion.id == 1).first()
    if ver:
        ver.version += 1
    else:
        db.add(ConfigVersion(id=1, version=2))
    db.commit()


@router.get("")
def list_admins(db: Session = Depends(get_db)):
    rows = db.query(Admin).order_by(Admin.tg_id.asc()).all()
    return [
        {
            "tg_id": a.tg_id,
            "name": a.name or "",
            "role": a.role,
            "username": a.username or ""
        }
        for a in rows
    ]


@router.post("")
def add_admin(
    data: AdminCreate,
    user_payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    existing = db.query(Admin).filter(Admin.tg_id == data.tg_id).first()
    pwd_hash = get_password_hash(data.password) if data.password else None

    if existing:
        existing.name = data.name or existing.name
        existing.role = data.role or existing.role
        if data.username:
            existing.username = data.username
        if pwd_hash:
            existing.password_hash = pwd_hash
    else:
        admin = Admin(
            tg_id=data.tg_id,
            name=data.name or "",
            role=data.role,
            username=data.username,
            password_hash=pwd_hash
        )
        db.add(admin)

    db.commit()
    bump_version(db)

    actor_id = int(user_payload.get("sub", 0))
    log_audit(db, actor_id, "ADMIN_CREATE_UPDATE", str(data.tg_id), {"name": data.name, "role": data.role})

    return {"status": "success", "tg_id": data.tg_id}


@router.delete("/{tg_id}")
def delete_admin(
    tg_id: int,
    user_payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    admin = db.query(Admin).filter(Admin.tg_id == tg_id).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin topilmadi")

    actor_id = int(user_payload.get("sub", 0))
    if actor_id == tg_id:
        raise HTTPException(status_code=400, detail="O'zingizni o'chira olmaysiz")

    db.delete(admin)
    db.commit()
    bump_version(db)

    log_audit(db, actor_id, "ADMIN_DELETE", str(tg_id), {"name": admin.name})
    return {"status": "success", "message": "Admin o'chirildi"}
