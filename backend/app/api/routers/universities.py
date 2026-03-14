from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import University

router = APIRouter(prefix="/universities", tags=["universities"])


@router.get("/")
def list_universities(db: Session = Depends(get_db)):
    universities = db.query(University).all()
    return [
        {
            "id": u.id,
            "name": u.name,
            "slug": u.slug,
            "is_crawled": u.is_crawled,
            "crawled_at": u.crawled_at,
        }
        for u in universities
    ]
