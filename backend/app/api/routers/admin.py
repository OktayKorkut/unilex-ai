from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, field_validator
from sqlalchemy import func
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import Generic, Optional, TypeVar

from app.db.database import get_db
from app.db.models import User, University, Document, ChatSession, Message, SystemLog
from app.api.deps import get_current_admin
from app.rag.embedder import _get_qdrant, COLLECTION_NAME
from app.services.system_log_service import get_system_logs
from qdrant_client.models import Filter, FieldCondition, MatchValue

router = APIRouter(prefix="/admin", tags=["admin"])

T = TypeVar("T")


class Paginated(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int


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


@router.get("/users", response_model=Paginated[UserAdminResponse])
def list_users(
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    q = db.query(User).order_by(User.created_at.desc())
    total = q.count()
    items = q.offset(offset).limit(limit).all()
    return Paginated(items=items, total=total, limit=limit, offset=offset)


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


@router.get("/documents", response_model=Paginated[DocumentAdminResponse])
def list_documents(
    university_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    q = db.query(Document)
    if university_id is not None:
        q = q.filter(Document.university_id == university_id)
    q = q.order_by(Document.created_at.desc())
    total = q.count()
    items = q.offset(offset).limit(limit).all()
    return Paginated(items=items, total=total, limit=limit, offset=offset)


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


class SystemLogResponse(BaseModel):
    id: int
    level: str
    title: str
    message: str
    created_at: datetime

    @field_validator('created_at', mode='before')
    @classmethod
    def ensure_tz(cls, v):
        if isinstance(v, datetime) and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    class Config:
        from_attributes = True


@router.get("/logs", response_model=Paginated[SystemLogResponse])
def list_system_logs(
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
    limit: int = Query(15, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    q = db.query(SystemLog).order_by(SystemLog.created_at.desc())
    total = q.count()
    items = q.offset(offset).limit(limit).all()
    return Paginated(items=items, total=total, limit=limit, offset=offset)


class LoadHistoryPoint(BaseModel):
    hour_utc: datetime
    chat_count: int
    event_count: int

    @field_validator('hour_utc', mode='before')
    @classmethod
    def ensure_tz(cls, v):
        if isinstance(v, datetime) and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    class Config:
        from_attributes = True


@router.get("/load-history", response_model=list[LoadHistoryPoint])
def get_load_history(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    start = now - timedelta(hours=23)

    chat_rows = db.query(
        func.date_trunc('hour', Message.created_at).label('hour'),
        func.count(Message.id).label('cnt'),
    ).filter(
        Message.role == 'user',
        Message.created_at >= start,
    ).group_by('hour').all()

    event_rows = db.query(
        func.date_trunc('hour', SystemLog.created_at).label('hour'),
        func.count(SystemLog.id).label('cnt'),
    ).filter(SystemLog.created_at >= start).group_by('hour').all()

    chat_map = {r.hour.replace(tzinfo=timezone.utc): r.cnt for r in chat_rows}
    event_map = {r.hour.replace(tzinfo=timezone.utc): r.cnt for r in event_rows}

    points = []
    for i in range(24):
        h = start + timedelta(hours=i)
        points.append(LoadHistoryPoint(
            hour_utc=h,
            chat_count=chat_map.get(h, 0),
            event_count=event_map.get(h, 0),
        ))
    return points

