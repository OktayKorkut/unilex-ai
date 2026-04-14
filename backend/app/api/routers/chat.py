from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.database import get_db
from app.db.models import ChatSession, University, User
from app.api.deps import get_current_user

router = APIRouter(prefix="/chat", tags=["chat"])


class SessionCreate(BaseModel):
    university_id: int

class SessionCreateResponse(BaseModel):
    message: str
    session_id: int
    university_id: int
    created_at: datetime
    
class SessionListResponse(BaseModel):
    id: int
    university_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class MessageDetailResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

class SessionDetailResponse(BaseModel):
    id: int
    university_id: int
    created_at: datetime
    messages: list[MessageDetailResponse]

    class Config:
        from_attributes = True

@router.post("/sessions", status_code=status.HTTP_201_CREATED, response_model=SessionCreateResponse)
def create_chat_session(
    data: SessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    university = db.query(University).filter(University.id == data.university_id).first()
    if not university:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Böyle bir üniversite sistemde bulunamadı"
        )

    new_session = ChatSession(
        user_id=current_user.id,
        university_id=data.university_id
    )
    
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return {
        "message": "Chat session başarıyla oluşturuldu",
        "session_id": new_session.id,
        "university_id": new_session.university_id,
        "created_at": new_session.created_at
    }


@router.get("/sessions", response_model=list[SessionListResponse])
def get_chat_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sessions = db.query(ChatSession).filter(ChatSession.user_id == current_user.id).order_by(ChatSession.created_at.desc()).all()
    
    return sessions


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
def get_chat_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Oturum bulunamadı veya bu oturuma erişim yetkiniz yok"
        )
        
    return session


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Oturum bulunamadı veya silme yetkiniz yok"
        )

    db.delete(session)
    db.commit()
    
    return None
