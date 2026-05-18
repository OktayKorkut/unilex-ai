from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.db.database import get_db
from app.db.models import User, University, Document, ChatSession, Message
from app.api.deps import get_current_admin
from app.rag.embedder import _get_qdrant, COLLECTION_NAME
from qdrant_client.models import Filter, FieldCondition, MatchValue

router = APIRouter(prefix="/admin", tags=["admin"])


class UserAdminResponse(BaseModel):
    id: int
    email: str
    full_name: str
    is_admin: bool
    university_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentAdminResponse(BaseModel):
    id: int
    university_id: int
    title: str
    source_url: str
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    crawl_counts = {}
    for row in db.query(University.crawl_status).all():
        crawl_counts[row.crawl_status] = crawl_counts.get(row.crawl_status, 0) + 1

    return {
        "users": db.query(User).count(),
        "universities": db.query(University).count(),
        "documents": db.query(Document).count(),
        "chat_sessions": db.query(ChatSession).count(),
        "crawl_status_breakdown": crawl_counts,
    }


@router.get("/users", response_model=list[UserAdminResponse])
def list_users(
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    if user_id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Kendi hesabınızı bu endpoint ile silemezsiniz")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    session_ids = [row.id for row in db.query(ChatSession.id).filter(ChatSession.user_id == user_id).all()]
    if session_ids:
        db.query(Message).filter(Message.session_id.in_(session_ids)).delete(synchronize_session=False)
        db.query(ChatSession).filter(ChatSession.id.in_(session_ids)).delete(synchronize_session=False)

    db.delete(user)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/documents", response_model=list[DocumentAdminResponse])
def list_documents(
    university_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    q = db.query(Document)
    if university_id is not None:
        q = q.filter(Document.university_id == university_id)
    return q.order_by(Document.created_at.desc()).all()


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    try:
        qdrant = _get_qdrant()
        qdrant.delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(
                must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
            ),
        )
    except Exception:
        pass

    db.delete(document)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/users/{user_id}/promote", response_model=UserAdminResponse)
def promote_user(
    user_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.is_admin = True
    db.commit()
    db.refresh(user)
    return user
