from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.db.database import get_db
from app.api.deps import get_current_user
from app.db.models import User, University, ChatSession, Message

router = APIRouter(prefix="/users", tags=["users"])


class UserProfileResponse(BaseModel):
    id: int
    email: str
    full_name: str
    university_id: Optional[int]

    class Config:
        from_attributes = True

class UserUniversityUpdate(BaseModel):
    university_id: int

@router.get("/me", response_model=UserProfileResponse)
def get_user_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserProfileResponse)
def update_user_university(
    data: UserUniversityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    
    university = db.query(University).filter(University.id == data.university_id).first()
    if not university:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Seçtiğiniz üniversite veritabanında bulunamadı"
        )
    
    # Kullanıcının university_id bilgisini güncelleyip kaydediyoruz
    current_user.university_id = data.university_id
    db.commit()
    db.refresh(current_user)

    return current_user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session_ids = (
        db.query(ChatSession.id)
        .filter(ChatSession.user_id == current_user.id)
        .all()
    )
    if session_ids:
        ids = [row.id for row in session_ids]
        db.query(Message).filter(Message.session_id.in_(ids)).delete(synchronize_session=False)
        db.query(ChatSession).filter(ChatSession.id.in_(ids)).delete(synchronize_session=False)

    db.delete(current_user)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
