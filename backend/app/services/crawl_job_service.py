"""
Arka plan crawl job'u.

FastAPI BackgroundTasks tarafından çağrılır; kendi SQLAlchemy session'ını
yönetir ve request session'ına bağımlı değildir.
"""

from app.core.logger import get_logger
from app.db.database import SessionLocal
from app.db.models import University, Document
from app.crawler.university_crawler import UniversityCrawler
from app.crawler.mevzuat_discovery import discover_mevzuat_url
from app.rag.embedder import embed_university_documents, _get_qdrant, COLLECTION_NAME
from app.services.system_log_service import create_system_log
from qdrant_client.models import Filter, FieldCondition, MatchValue
from sqlalchemy.orm import Session

logger = get_logger("crawl_job")


def _remove_obsolete_documents(db: Session, university_id: int, fresh_urls: set[str]) -> int:
    """DB'deki belgelerden yeni crawl'da bulunmayanları Qdrant + DB'den siler."""
    obsolete = (
        db.query(Document)
        .filter(Document.university_id == university_id)
        .filter(Document.source_url.notin_(fresh_urls))
        .all()
    )
    if not obsolete:
        return 0

    total = db.query(Document).filter(Document.university_id == university_id).count()
    if len(obsolete) / max(total, 1) > 0.8:
        create_system_log(
            db, "warning", "Obsolete Cleanup İptal",
            f"Şüpheli crawl: {len(obsolete)}/{total} belge silinecekti, güvenlik eşiği aşıldı, silme iptal edildi.",
        )
        return 0

    qdrant = _get_qdrant()
    for doc in obsolete:
        try:
            qdrant.delete(
                collection_name=COLLECTION_NAME,
                points_selector=Filter(
                    must=[FieldCondition(key="document_id", match=MatchValue(value=doc.id))]
                ),
            )
        except Exception:
            pass
        db.delete(doc)
    db.commit()
    return len(obsolete)


async def run_crawl_job(university_id: int, *, cleanup_obsolete: bool = False) -> None:
    """
    Üniversite için crawl + embed pipeline'ını arka planda çalıştırır.

    Adımlar:
      1. Crawl (Playwright ile PDF linkleri + içerik)
      2. Belge çıkmazsa URL keşfi ve yeniden crawl
      3. Tüm belgeleri Qdrant'a embed et
      4. university.crawl_status'u güncelle ("done" veya "error")
    """
    db = SessionLocal()
    op = logger.start_operation("crawl_background_job")
    op.add_field("university_id", university_id)

    try:
        university = db.query(University).filter(University.id == university_id).first()
        if not university:
            op.add_field("result", "not_found").fail(exc_info=False)
            return

        create_system_log(db, "info", "Crawler Senkronizasyonu", f"{university.name} için web tarama (crawl) işlemi başlatıldı.")

        crawler = UniversityCrawler()
        result = await crawler.crawl(university, db)
        docs_added = result.get("documents_added", 0)
        op.add_field("docs_added", docs_added)

        if docs_added == 0:
            try:
                discovered_url = await discover_mevzuat_url(university.mevzuat_url)
            except Exception:
                discovered_url = None

            if discovered_url and discovered_url != university.mevzuat_url:
                op.add_field("discovered_url", discovered_url)
                university.mevzuat_url = discovered_url
                university.is_crawled = False
                db.commit()
                result = await crawler.crawl(university, db)
                op.add_field("retry_docs", result.get("documents_added", 0))
                docs_added = result.get("documents_added", 0)

        if cleanup_obsolete:
            fresh_urls = set(result.get("discovered_source_urls", []))
            if fresh_urls:
                removed = _remove_obsolete_documents(db, university_id, fresh_urls)
                op.add_field("obsolete_removed", removed)
                if removed:
                    create_system_log(
                        db, "info", "Crawler Senkronizasyonu",
                        f"{university.name} için {removed} eskimiş belge kaldırıldı.",
                    )

        chunks = embed_university_documents(university.id, db)
        op.add_field("chunks_embedded", chunks)

        db.refresh(university)
        university.crawl_status = "done"
        university.crawl_error = None
        db.commit()

        create_system_log(db, "info", "Crawler Senkronizasyonu", f"{university.name} kütüphane veritabanı başarıyla güncellendi. ({docs_added} yeni belge eklendi)")
        op.succeed()

    except Exception as e:
        op.fail()
        try:
            db.rollback()
            univ = db.query(University).filter(University.id == university_id).first()
            if univ:
                univ.crawl_status = "error"
                univ.crawl_error = str(e)[:500]
                db.commit()
                create_system_log(db, "error", "Crawler Senkronizasyonu", f"{univ.name} tarama işleminde hata oluştu: {str(e)[:250]}")
        except Exception:
            pass

    finally:
        db.close()
