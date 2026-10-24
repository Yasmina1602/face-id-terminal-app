import os
from zoneinfo import ZoneInfo
from pydantic_settings import BaseSettings

# Birinchi telegram_bot/.env, keyin .env.web dan qidirish
_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
_tb_env = os.path.join(_root_dir, "telegram_bot", ".env")
_web_env = os.path.join(_root_dir, "web", ".env.web")

_env_files = []
if os.path.exists(_tb_env):
    _env_files.append(_tb_env)
if os.path.exists(_web_env):
    _env_files.append(_web_env)


class Settings(BaseSettings):
    APP_ENV: str = "development"
    SECRET_KEY: str = "super-secret-key-change-in-production-davomat-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 720  # 12 soat

    # Ma'lumotlar bazasi
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 5432
    DB_NAME: str = "face_id_terminal"
    DB_USER: str = "root"
    DB_PASS: str = "1234"
    DB_POOL_SIZE: int = 3
    DB_MAX_OVERFLOW: int = 2

    # Telegram bot
    TELEGRAM_BOT_TOKEN: str = ""

    # Vaqt mintaqasi
    TZ_NAME: str = "Asia/Tashkent"

    # Server porti
    WEB_PORT: int = 8090
    WEB_HOST: str = "0.0.0.0"

    class Config:
        env_file = _env_files if _env_files else ".env"
        extra = "allow"

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.TZ_NAME)


settings = Settings()
