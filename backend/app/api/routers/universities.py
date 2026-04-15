from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.database import get_db
from app.db.models import University
from app.api.deps import get_current_user

router = APIRouter(prefix="/universities", tags=["universities"])


class UniversityCreate(BaseModel):
    name: str
    slug: str
    mevzuat_url: str

class UniversityListResponse(BaseModel):
    id: int
    name: str
    slug: str
    is_crawled: bool
    crawled_at: datetime | None = None

    class Config:
        from_attributes = True

class UniversityDetailResponse(BaseModel):
    id: int
    name: str
    slug: str
    mevzuat_url: str
    is_crawled: bool
    crawled_at: datetime | None = None

    class Config:
        from_attributes = True

class UniversityCreateResponse(BaseModel):
    message: str
    id: int


@router.get("/", response_model=list[UniversityListResponse])
def list_universities(db: Session = Depends(get_db)):
    universities = db.query(University).all()
    return universities


@router.get("/{uni_id}", response_model=UniversityDetailResponse)
def get_university(uni_id: int, db: Session = Depends(get_db)):
    university = db.query(University).filter(University.id == uni_id).first()
    if not university:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="University not found")
    return university


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=UniversityCreateResponse)
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
