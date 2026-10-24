import hmac
import hashlib
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Parollarni xeshlash (Argon2 asosiy, bcrypt zaxira)
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")
security_bearer = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    now_utc = datetime.now(timezone.utc)
    if expires_delta:
        expire = now_utc + expires_delta
    else:
        expire = now_utc + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": now_utc})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def verify_telegram_data(data: Dict[str, Any], bot_token: str) -> bool:
    """
    Telegram Login Widget HMAC-SHA256 tekshiruvi.
    auth_date <= 24 soat bo'lishi shart.
    """
    if not bot_token:
        return False

    received_hash = data.get("hash")
    if not received_hash:
        return False

    auth_date = int(data.get("auth_date", 0))
    now = int(time.time())
    if abs(now - auth_date) > 86400:  # 24 soatdan eski
        return False

    # Tekshirish qatorini tuzish (hash dan tashqari kalitlar alifbo tartibida)
    check_pairs = []
    for k in sorted(data.keys()):
        if k != "hash" and data[k] is not None:
            check_pairs.append(f"{k}={data[k]}")
    data_check_string = "\n".join(check_pairs)

    secret_key = hashlib.sha256(bot_token.encode("utf-8")).digest()
    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(calculated_hash, received_hash)


def get_current_user_payload(
    request: Request,
    bearer: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer)
) -> dict:
    """
    Sessiya tokenini Cookie yoki Authorization Bearer sarlavhasidan oladi.
    """
    token = None
    if bearer and bearer.credentials:
        token = bearer.credentials
    else:
        token = request.cookies.get("davomat_session")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tizimga kirish talab etiladi"
        )

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessiya muddati tugagan yoki token yaroqsiz"
        )
    return payload


def require_role(allowed_roles: list[str]):
    def role_checker(payload: dict = Depends(get_current_user_payload)) -> dict:
        user_role = payload.get("role", "viewer")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Ushbu amalni bajarish uchun ruxsat yetarli emas"
            )
        return payload
    return role_checker


# Qulay dependencylar
require_viewer = require_role(["admin", "viewer"])
require_admin = require_role(["admin"])
