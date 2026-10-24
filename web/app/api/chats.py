from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import require_admin, get_current_user_payload
from app.db.session import get_db
from app.db.models import Chat, ConfigVersion
from app.services.audit import log_audit

router = APIRouter(prefix="/chats", tags=["Telegram Guruhlar"], dependencies=[Depends(require_admin)])


def bump_version(db: Session):
    ver = db.query(ConfigVersion).filter(ConfigVersion.id == 1).first()
    if ver:
        ver.version += 1
    else:
        db.add(ConfigVersion(id=1, version=2))
    db.commit()


@router.get("")
def list_chats(db: Session = Depends(get_db)):
    chats = db.query(Chat).order_by(Chat.chat_id.asc()).all()
    return [{"chat_id": c.chat_id, "title": c.title or ""} for c in chats]


@router.delete("/{chat_id}")
def remove_chat(
    chat_id: int,
    user_payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    chat = db.query(Chat).filter(Chat.chat_id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Guruh topilmadi")

    db.delete(chat)
    db.commit()
    bump_version(db)

    actor_id = int(user_payload.get("sub", 0))
    log_audit(db, actor_id, "CHAT_DELETE", str(chat_id), {"title": chat.title})
    return {"status": "success", "message": "Guruh uzildi"}
