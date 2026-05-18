"""
Arka plan crawl job'u.

FastAPI BackgroundTasks tarafından çağrılır; kendi SQLAlchemy session'ını
yönetir ve request session'ına bağımlı değildir.
"""

from app.core.logger import get_logger
from app.db.database import SessionLocal
from app.db.models import University
from app.crawler.university_crawler import UniversityCrawler
from app.crawler.mevzuat_discovery import discover_mevzuat_url
from app.rag.embedder import embed_university_documents

logger = get_logger("crawl_job")


async def run_crawl_job(university_id: int) -> None:
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

        chunks = embed_university_documents(university.id, db)
        op.add_field("chunks_embedded", chunks)

        db.refresh(university)
        university.crawl_status = "done"
        university.crawl_error = None
        db.commit()
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
        except Exception:
            pass

    finally:
        db.close()
