from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import University
from app.api.routers.auth import get_current_user

router = APIRouter(prefix="/universities", tags=["universities"])


class UniversityCreate(BaseModel):
    name: str
    slug: str
    mevzuat_url: str


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


@router.get("/{uni_id}")
def get_university(uni_id: int, db: Session = Depends(get_db)):
    university = db.query(University).filter(University.id == uni_id).first()
    if not university:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="University not found")
    return {
        "id": university.id,
        "name": university.name,
        "slug": university.slug,
        "mevzuat_url": university.mevzuat_url,
        "is_crawled": university.is_crawled,
        "crawled_at": university.crawled_at,
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_university(
    data: UniversityCreate, 
    db: Session = Depends(get_db), 
    user = Depends(get_current_user)
):
    existing = db.query(University).filter(
        (University.slug == data.slug) | (University.name == data.name)
    ).first()
    
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="University already exists")
    
    new_uni = University(
        name=data.name,
        slug=data.slug,
        mevzuat_url=data.mevzuat_url
    )
    db.add(new_uni)
    db.commit()
    db.refresh(new_uni)
    
    return {"message": "University created successfully", "id": new_uni.id}
