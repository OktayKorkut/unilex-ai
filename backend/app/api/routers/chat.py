from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.db.database import get_db
from app.db.models import ChatSession, University, User
from app.api.deps import get_current_user
from app.core.exceptions import SessionNotFoundError, UniversityNotFoundError
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
    created_at: datetime

    class Config:
        from_attributes = True


class MessageDetailResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime
    sources: Optional[list[dict]] = None

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
    question: str
    answer: str
    university_id: Optional[int]
    sources: list[dict]


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

    # Üniversite henüz belirlenmemişse mesajdan tespit et ve hazırla
    if session.university_id is None:
        university, error_msg = await UniversityService.resolve_for_session(
            session, data.content, db
        )
        if university is None:
            ChatService.save_messages(session_id, data.content, error_msg, db)
            op.add_field("result", "university_unresolved").fail(exc_info=False)
            return {
                "question": data.content,
                "answer": error_msg,
                "university_id": None,
                "sources": [],
            }
        op.add_field("university_id", university.id)

    # Soruyu yanıtla
    answer, sources = await ChatService.answer_question(session, data.content, db)
    ChatService.save_messages(session_id, data.content, answer, db, sources=sources)

    op.add_field("university_id", session.university_id).add_field("sources", len(sources)).succeed()
    return {
        "question": data.content,
        "answer": answer,
        "university_id": session.university_id,
        "sources": sources,
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
