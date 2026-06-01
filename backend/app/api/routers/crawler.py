from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import University, Document
from app.api.deps import get_current_user
from app.core.logger import get_logger
from app.rag.embedder import embed_university_documents
from app.services.crawl_job_service import run_crawl_job

router = APIRouter(prefix="/universities", tags=["crawler"])
logger = get_logger("crawler_router")


@router.post("/{university_id}/crawl", status_code=status.HTTP_202_ACCEPTED)
async def crawl_university(
    university_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Üniversite için crawl + embed işlemini arka planda başlatır.
    Hemen 202 döner; ilerlemeyi GET /universities/{id}/crawl-status ile takip et.
    """
    university = db.query(University).filter(University.id == university_id).first()
    if not university:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="University not found")

    if university.crawl_status == "running":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu üniversite için zaten bir crawl çalışıyor.",
        )

    university.crawl_status = "running"
    university.crawl_error = None
    db.commit()

    background_tasks.add_task(run_crawl_job, university_id, cleanup_obsolete=True)
    op = logger.start_operation("crawl_triggered")
    op.add_field("university_id", university_id).succeed()

    return {
        "message": "Crawl arka planda başlatıldı.",
        "university_id": university_id,
        "crawl_status": "running",
    }


@router.get("/{university_id}/crawl-status")
def get_crawl_status(
    university_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Crawl job'unun mevcut durumunu ve belge istatistiklerini döner."""
    university = db.query(University).filter(University.id == university_id).first()
    if not university:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="University not found")

    doc_count = db.query(Document).filter(Document.university_id == university_id).count()

    return {
        "university_id": university_id,
        "name": university.name,
        "crawl_status": university.crawl_status,
        "is_crawled": university.is_crawled,
        "crawled_at": university.crawled_at,
        "document_count": doc_count,
        "crawl_error": university.crawl_error,
    }


@router.post("/{university_id}/embed", status_code=status.HTTP_202_ACCEPTED)
def embed_university(
    university_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Mevcut belgeleri Qdrant'a embed eder (crawl gerektirmez)."""
    university = db.query(University).filter(University.id == university_id).first()
    if not university:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="University not found")

    def _embed_task():
        from app.db.database import SessionLocal
        task_db = SessionLocal()
        try:
            embed_university_documents(university_id, task_db)
        finally:
            task_db.close()

    background_tasks.add_task(_embed_task)
    return {"message": "Embed arka planda başlatıldı.", "university_id": university_id}
