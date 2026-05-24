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


import io
from fastapi import UploadFile, File
from pypdf import PdfReader
from app.api.deps import get_current_admin
from app.db.models import User
from app.rag.embedder import embed_document
from app.services.system_log_service import create_system_log


@router.post("/universities/{university_id}/upload-pdf", status_code=status.HTTP_201_CREATED)
async def upload_university_pdf(
    university_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    university = db.query(University).filter(University.id == university_id).first()
    if not university:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Üniversite bulunamadı."
        )

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Yalnızca PDF dosyaları yüklenebilir."
        )

    try:
        pdf_content = await file.read()
        pdf_file = io.BytesIO(pdf_content)
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"

        if not text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PDF dosyasından metin okunamadı. Lütfen taranmış (resim formatındaki) belgeler yerine dijital PDF dosyaları yükleyin."
            )

        # Create Document
        document = Document(
            university_id=university_id,
            title=file.filename,
            content=text,
            source_url=f"Uploaded: {file.filename}"
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        # Embed Document in Qdrant
        try:
            embed_document(document)
            create_system_log(
                db,
                "info",
                "Crawler Senkronizasyonu",
                f"Yeni yönetmelik PDF yükleme yoluyla indekslendi: {file.filename} ({university.name})"
            )
        except Exception as embed_err:
            create_system_log(
                db,
                "error",
                "Vektör DB Hatası",
                f"Yüklenen {file.filename} belgesi indekslenirken hata: {str(embed_err)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Belge veritabanına kaydedildi ancak vektör çıkarımı başarısız oldu: {str(embed_err)}"
            )

        return {
            "message": "Belge başarıyla yüklendi ve indekslendi.",
            "document_id": document.id,
            "title": document.title
        }

    except HTTPException:
        raise
    except Exception as e:
        create_system_log(
            db,
            "error",
            "Crawler Senkronizasyonu",
            f"PDF yükleme işleminde hata: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF işlenirken bir hata oluştu: {str(e)}"
        )

