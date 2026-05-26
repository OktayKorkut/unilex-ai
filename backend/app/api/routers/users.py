from fastapi import APIRouter, Depends, HTTPException, status, Response, File, UploadFile, Request
import os
import shutil
import uuid
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
    history_saved: bool
    anonymized: bool
    avatar_url: Optional[str]

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    university_id: Optional[int] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    history_saved: Optional[bool] = None
    anonymized: Optional[bool] = None
    avatar_url: Optional[str] = None

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

    if data.history_saved is not None:
        current_user.history_saved = data.history_saved

    if data.anonymized is not None:
        current_user.anonymized = data.anonymized

    if data.avatar_url is not None:
        current_user.avatar_url = data.avatar_url.strip() or None

    db.commit()
    db.refresh(current_user)

    return current_user


@router.post("/me/avatar", response_model=UserProfileResponse)
def upload_avatar(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Yalnızca JPEG, PNG, GIF veya WEBP formatındaki resimler yüklenebilir."
        )
    
    static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "static")
    avatars_dir = os.path.join(static_dir, "avatars")
    os.makedirs(avatars_dir, exist_ok=True)
    
    ext = os.path.splitext(file.filename)[1]
    if not ext:
        if file.content_type == "image/jpeg":
            ext = ".jpg"
        elif file.content_type == "image/png":
            ext = ".png"
        elif file.content_type == "image/gif":
            ext = ".gif"
        elif file.content_type == "image/webp":
            ext = ".webp"
        else:
            ext = ".png"

    filename = f"avatar_{current_user.id}_{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(avatars_dir, filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dosya kaydedilirken bir hata oluştu: {str(e)}"
        )
        
    base_url = str(request.base_url).rstrip('/')
    avatar_url = f"{base_url}/static/avatars/{filename}"
    
    current_user.avatar_url = avatar_url
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
