from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import re

from app.db.database import get_db
from app.db.models import ChatSession, Message, University, User
from app.api.deps import get_current_user
from app.core.exceptions import MessageNotFoundError, SessionNotFoundError, UniversityNotFoundError
from app.core.logger import get_logger
from app.services.university_service import UniversityService
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])
logger = get_logger("chat_router")


# ---------------------------------------------------------------------------
# Pydantic şemaları
# ---------------------------------------------------------------------------

class SessionCreate(BaseModel):
    university_id: Optional[int] = None


class SessionCreateResponse(BaseModel):
    message: str
    session_id: int
    university_id: Optional[int]
    created_at: datetime


class SessionListResponse(BaseModel):
    id: int
    university_id: Optional[int]
    title: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class MessageDetailResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime
    sources: Optional[list[dict]] = None
    feedback_rating: Optional[str] = None
    feedback_id: Optional[int] = None

    class Config:
        from_attributes = True


class SessionDetailResponse(BaseModel):
    id: int
    university_id: Optional[int]
    created_at: datetime
    messages: list[MessageDetailResponse]

    class Config:
        from_attributes = True


class MessageRequest(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: Optional[int] = None
    question: str
    answer: str
    university_id: Optional[int]
    sources: list[dict]
    session_title: Optional[str] = None


def mask_pii(text: str) -> str:
    # 1. E-mail regex
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    text = re.sub(email_pattern, '[E-POSTA]', text)

    # 2. Turkish phone format regex
    # Handles: +90 5xx xxx xx xx, 05xx xxx xx xx, 5xx-xxx-xxxx, etc.
    phone_pattern = r'(?:\+?90[-. ]?)?\(?0?[5-9][0-9]{2}\)?[-. ]?[0-9]{3}[-. ]?[0-9]{2}[-. ]?[0-9]{2}'
    text = re.sub(phone_pattern, '[TELEFON]', text)

    # 3. 11-digit Turkish National ID (TC Kimlik No)
    tc_pattern = r'\b[1-9][0-9]{10}\b'
    text = re.sub(tc_pattern, '[TC KİMLİK NO]', text)

    return text


# ---------------------------------------------------------------------------
# Endpoint'ler
# ---------------------------------------------------------------------------

@router.post("/sessions", status_code=status.HTTP_201_CREATED, response_model=SessionCreateResponse)
async def create_chat_session(
    data: SessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    op = logger.start_operation("create_chat_session")

    if data.university_id is not None:
        university = db.query(University).filter(University.id == data.university_id).first()
        if not university:
            op.fail(exc_info=False)
            raise UniversityNotFoundError()

    new_session = ChatSession(user_id=current_user.id, university_id=data.university_id)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    op.add_field("session_id", new_session.id).succeed()
    return {
        "message": "Chat session başarıyla oluşturuldu",
        "session_id": new_session.id,
        "university_id": new_session.university_id,
        "created_at": new_session.created_at,
    }


@router.get("/sessions", response_model=list[SessionListResponse])
async def get_chat_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id
    ).order_by(ChatSession.created_at.desc()).all()


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_chat_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id,
    ).first()
    if not session:
        raise SessionNotFoundError()
    return session


@router.post("/sessions/{session_id}/messages", response_model=MessageResponse)
async def send_message(
    session_id: int,
    data: MessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    op = logger.start_operation("send_message")
    op.add_field("session_id", session_id)

    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id,
    ).first()
    if not session:
        op.fail(exc_info=False)
        raise SessionNotFoundError()

    content_to_process = data.content
    if current_user.anonymized:
        content_to_process = mask_pii(content_to_process)

    # Üniversite henüz belirlenmemişse mesajdan tespit et ve hazırla
    if session.university_id is None:
        university, error_msg = await UniversityService.resolve_for_session(
            session, content_to_process, db
        )
        if university is None:
            if current_user.history_saved:
                ChatService.save_messages(session_id, content_to_process, error_msg, db)
            op.add_field("result", "university_unresolved").fail(exc_info=False)
            return {
                "question": content_to_process,
                "answer": error_msg,
                "university_id": None,
                "sources": [],
            }
        op.add_field("university_id", university.id)

    # Soruyu yanıtla
    answer, sources = await ChatService.answer_question(session, content_to_process, db)

    assistant_msg_id = None
    # İlk mesajsa GPT ile sohbet başlığı üret
    if current_user.history_saved:
        if session.title is None:
            session.title = ChatService.generate_title(content_to_process)
            db.commit()

        saved_msg = ChatService.save_messages(session_id, content_to_process, answer, db, sources=sources)
        assistant_msg_id = saved_msg.id

    op.add_field("university_id", session.university_id).add_field("sources", len(sources)).succeed()
    return {
        "id": assistant_msg_id,
        "question": content_to_process,
        "answer": answer,
        "university_id": session.university_id,
        "sources": sources,
        "session_title": session.title,
    }


@router.post("/sessions/{session_id}/messages/{message_id}/regenerate", response_model=MessageResponse)
async def regenerate_message(
    session_id: int,
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    op = logger.start_operation("regenerate_message")
    op.add_field("session_id", session_id).add_field("message_id", message_id)

    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id,
    ).first()
    if not session:
        op.fail(exc_info=False)
        raise SessionNotFoundError()

    assistant_msg = db.query(Message).filter(
        Message.id == message_id,
        Message.session_id == session_id,
        Message.role == "assistant",
    ).first()
    if not assistant_msg:
        op.fail(exc_info=False)
        raise MessageNotFoundError()

    all_messages = (
        db.query(Message)
        .filter(Message.session_id == session_id)
        .order_by(Message.created_at)
        .all()
    )

    assistant_idx = next((i for i, m in enumerate(all_messages) if m.id == message_id), None)
    if assistant_idx is None or assistant_idx == 0 or all_messages[assistant_idx - 1].role != "user":
        op.fail(exc_info=False)
        raise MessageNotFoundError()

    user_msg = all_messages[assistant_idx - 1]
    question = user_msg.content
    history = [{"role": m.role, "content": m.content} for m in all_messages[:assistant_idx - 1]]

    db.delete(assistant_msg)
    db.commit()

    answer, sources = await ChatService.answer_question(session, question, db, history=history)

    new_msg = None
    if current_user.history_saved:
        new_msg = ChatService.save_assistant_message(session_id, answer, db, sources=sources)

    op.add_field("university_id", session.university_id).add_field("sources", len(sources)).succeed()
    return {
        "id": new_msg.id if new_msg else None,
        "question": question,
        "answer": answer,
        "university_id": session.university_id,
        "sources": sources,
        "session_title": session.title,
    }


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id,
    ).first()
    if not session:
        raise SessionNotFoundError()
    db.delete(session)
    db.commit()
    return None
