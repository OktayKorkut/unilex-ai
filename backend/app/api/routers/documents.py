from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel
from app.db.database import get_db
from app.db.models import Document, University

router = APIRouter(tags=["documents"])

class DocumentListResponse(BaseModel):
    id: int
    title: str
    source_url: str
    created_at: datetime

    class Config:
        from_attributes = True

class DocumentDetailResponse(BaseModel):
    id: int
    university_id: int
    title: str
    content: str
    source_url: str
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/universities/{university_id}/documents", response_model=list[DocumentListResponse])
def get_university_documents(
    university_id: int, 
    db: Session = Depends(get_db)
):
    university = db.query(University).filter(University.id == university_id).first()
    if not university:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="University not found"
        )

    documents = db.query(Document).filter(Document.university_id == university_id).order_by(Document.created_at.desc()).all()
    
    return documents

@router.get("/documents/{document_id}", response_model=DocumentDetailResponse)
def get_document(
    document_id: int, 
    db: Session = Depends(get_db)
):
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Document not found"
        )
        
    return document
