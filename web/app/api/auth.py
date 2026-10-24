from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    verify_password, create_access_token, verify_telegram_data,
    get_current_user_payload
)
from app.db.session import get_db
from app.db.models import Admin
from app.services.audit import log_audit

router = APIRouter(prefix="/auth", tags=["Autentifikatsiya"])


class LoginRequest(BaseModel):
    username: str
    password: str


class TelegramAuthRequest(BaseModel):
    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None
    auth_date: int
    hash: str


@router.post("/login")
def login_with_password(
    req: LoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    admin = db.query(Admin).filter(Admin.username == req.username).first()
    if not admin or not admin.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Foydalanuvchi nomi yoki parol noto'g'ri"
        )

    if not verify_password(req.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Foydalanuvchi nomi yoki parol noto'g'ri"
        )

    payload = {
        "sub": str(admin.tg_id),
        "username": admin.username,
        "name": admin.name or admin.username,
        "role": admin.role
    }
    token = create_access_token(payload)

    # HttpOnly Cookie o'rnatish
    response.set_cookie(
        key="davomat_session",
        value=token,
        httponly=True,
        secure=settings.APP_ENV == "production",
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

    log_audit(db, admin.tg_id, "AUTH_LOGIN", "Web Login", {"username": req.username})

    return {
        "status": "success",
        "token": token,
        "user": payload
    }


@router.post("/telegram")
def login_with_telegram(
    req: TelegramAuthRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    if not settings.TELEGRAM_BOT_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Telegram bot token sozlanmagan"
        )

    data_dict = req.model_dump()
    if not verify_telegram_data(data_dict, settings.TELEGRAM_BOT_TOKEN):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Telegram ma'lumotlari haqiqiy emas yoki muddati tugagan"
        )

    admin = db.query(Admin).filter(Admin.tg_id == req.id).first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Siz tizim adminlari ro'yxatida emassiz"
        )

    payload = {
        "sub": str(admin.tg_id),
        "username": admin.username or req.username or "",
        "name": admin.name or f"{req.first_name or ''} {req.last_name or ''}".strip(),
        "role": admin.role
    }
    token = create_access_token(payload)

    response.set_cookie(
        key="davomat_session",
        value=token,
        httponly=True,
        secure=settings.APP_ENV == "production",
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

    log_audit(db, admin.tg_id, "AUTH_TELEGRAM", "Telegram Login", {"tg_id": req.id})

    return {
        "status": "success",
        "token": token,
        "user": payload
    }


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key="davomat_session")
    return {"status": "success", "message": "Tizimdan chiqildi"}


@router.get("/me")
def get_me(user_payload: dict = Depends(get_current_user_payload)):
    return {
        "id": user_payload.get("sub"),
        "username": user_payload.get("username"),
        "name": user_payload.get("name"),
        "role": user_payload.get("role")
    }
