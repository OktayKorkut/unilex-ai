from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Feedback
from app.api.deps import get_current_admin

router = APIRouter(tags=["feedbacks"])


# Pydantic schemas
class FeedbackCreate(BaseModel):
    full_name: str
    email: EmailStr
    message: str


class FeedbackResponse(BaseModel):
    id: int
    full_name: str
    email: str
    message: str
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


@router.get("/admin/feedbacks", response_model=list[FeedbackResponse])
def get_feedbacks(
    db: Session = Depends(get_db),
    admin_user=Depends(get_current_admin),
):
    # Retrieve feedbacks ordered by creation time descending
    feedbacks = db.query(Feedback).order_by(Feedback.created_at.desc()).all()
    return feedbacks
