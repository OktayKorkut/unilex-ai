from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.db.database import get_db
from app.api.deps import get_current_user
from app.db.models import User, University, ChatSession, Message

from app.core.security import hash_password

router = APIRouter(prefix="/users", tags=["users"])


class UserProfileResponse(BaseModel):
    id: int
    email: str
    full_name: str
    is_admin: bool
    university_id: Optional[int]

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    university_id: Optional[int] = None
    full_name: Optional[str] = None
    password: Optional[str] = None

@router.get("/me", response_model=UserProfileResponse)
def get_user_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserProfileResponse)
def update_user_profile(
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if data.university_id is not None:
        university = db.query(University).filter(University.id == data.university_id).first()
        if not university:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Seçtiğiniz üniversite veritabanında bulunamadı"
            )
        current_user.university_id = data.university_id

    if data.full_name is not None:
        if not data.full_name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="İsim alanı boş bırakılamaz"
            )
        current_user.full_name = data.full_name.strip()

    if data.password is not None and data.password != "":
        if len(data.password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Şifre en az 6 karakter olmalıdır"
            )
        current_user.hashed_password = hash_password(data.password)

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
