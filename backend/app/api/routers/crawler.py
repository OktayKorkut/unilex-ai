from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import University
from app.api.deps import get_current_user
from app.crawler.university_crawler import UniversityCrawler
from app.rag.embedder import embed_university_documents

router = APIRouter(prefix="/universities", tags=["crawler"])


@router.post("/{university_id}/crawl")
async def crawl_university(
    university_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    university = db.query(University).filter(University.id == university_id).first()
    if not university:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="University not found")

    crawler = UniversityCrawler()
    result = await crawler.crawl(university, db)

    return {
        "university": university.name,
        "mevzuat_url": university.mevzuat_url,
        "is_crawled": university.is_crawled,
        "crawled_at": university.crawled_at,
        "documents_added": result["documents_added"],
        "pdfs_found": result["pdfs_found"],
        "chunks_embedded": result.get("chunks_embedded", 0),
        "errors": result["errors"],
    }


@router.post("/{university_id}/embed")
def embed_university(
    university_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Mevcut belgeleri Qdrant'a embed eder (crawl gerektirmez)."""
    university = db.query(University).filter(University.id == university_id).first()
    if not university:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="University not found")

    chunks = embed_university_documents(university_id, db)
    return {"university": university.name, "chunks_embedded": chunks}
