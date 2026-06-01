from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Feedback, User
from app.api.deps import get_current_admin, get_current_user
from app.api.routers.admin import Paginated

router = APIRouter(tags=["feedbacks"])


# Pydantic schemas
class FeedbackCreate(BaseModel):
    full_name: str
    email: EmailStr
    message: str


class ChatFeedbackCreate(BaseModel):
    message_id: int
    user_question: str
    ai_response: str
    rating: str  # "Helpful" | "Not Helpful"
    comment: Optional[str] = None


class FeedbackResponse(BaseModel):
    id: int
    full_name: Optional[str] = None
    email: Optional[str] = None
    message: Optional[str] = None
    user_question: Optional[str] = None
    ai_response: Optional[str] = None
    rating: Optional[str] = None
    comment: Optional[str] = None
    message_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/feedbacks", status_code=status.HTTP_201_CREATED, response_model=FeedbackResponse)
def create_feedback(body: FeedbackCreate, db: Session = Depends(get_db)):
    feedback = Feedback(
        full_name=body.full_name,
        email=body.email,
        message=body.message,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


@router.post("/feedbacks/chat-feedback", status_code=status.HTTP_201_CREATED, response_model=FeedbackResponse)
def create_chat_feedback(
    body: ChatFeedbackCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    # Check if a feedback for this message_id already exists.
    existing_feedback = db.query(Feedback).filter(Feedback.message_id == body.message_id).first()
    if existing_feedback:
        existing_feedback.rating = body.rating
        existing_feedback.comment = body.comment
        db.commit()
        db.refresh(existing_feedback)
        return existing_feedback

    feedback = Feedback(
        message_id=body.message_id,
        user_question=body.user_question,
        ai_response=body.ai_response,
        rating=body.rating,
        comment=body.comment,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


@router.get("/admin/feedbacks", response_model=Paginated[FeedbackResponse])
def get_feedbacks(
    db: Session = Depends(get_db),
    admin_user=Depends(get_current_admin),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    q = db.query(Feedback).filter(Feedback.rating.is_(None)).order_by(Feedback.created_at.desc())
    total = q.count()
    items = q.offset(offset).limit(limit).all()
    return Paginated(items=items, total=total, limit=limit, offset=offset)


@router.get("/admin/bad-feedbacks", response_model=Paginated[FeedbackResponse])
def get_bad_feedbacks(
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    q = db.query(Feedback).filter(Feedback.rating == "Not Helpful").order_by(Feedback.created_at.desc())
    total = q.count()
    items = q.offset(offset).limit(limit).all()
    return Paginated(items=items, total=total, limit=limit, offset=offset)


@router.delete("/feedbacks/chat-feedback/{feedback_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat_feedback(
    feedback_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Geri bildirim bulunamadı."
        )
    db.delete(feedback)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


