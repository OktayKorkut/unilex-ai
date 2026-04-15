"""
Unilex AI — üniversite iş mantığı servisi.

Üniversite tespiti, oluşturma, crawl ve embed süreçlerini
router'dan ayırır; router sadece HTTP katmanı ile ilgilenir.
"""

from sqlalchemy.orm import Session

from app.core.logger import get_logger
from app.core.exceptions import CrawlFailedError
from app.db.models import University, Document
from app.agent.university_detector import detect_university
from app.agent.university_finder import find_or_create_university
from app.crawler.university_crawler import UniversityCrawler
from app.crawler.mevzuat_discovery import discover_mevzuat_url
from app.rag.embedder import embed_university_documents, COLLECTION_NAME

logger = get_logger("university_service")


class UniversityService:

    @staticmethod
    async def resolve_for_session(
        session,
        message: str,
        db: Session,
    ) -> tuple["University | None", str]:
        """
        Session'a bağlı üniversitenin hazır olmasını sağlar.

        Adımlar:
          1. Mesajdan üniversite tespiti (GPT + DB eşleşmesi)
          2. DB'de yoksa yeni üniversite oluşturma
          3. Crawl (gerekirse URL keşfi ile)
          4. Qdrant embed

        Returns:
            (university, error_msg)
            error_msg boşsa başarılı; doluysa kullanıcıya gösterilecek mesaj.
        """
        op = logger.start_operation("resolve_university_for_session")

        # 1. Mesajdan üniversite tespiti
        university, detected_name = detect_university(message, db)
        op.add_field("detected_name", detected_name)

        # 2. DB'de bulunamadıysa GPT ile oluştur
        if university is None and detected_name:
            university = find_or_create_university(detected_name, db)
            op.add_field("created_new", university is not None)

        if university is None:
            op.add_field("result", "detection_failed").fail(exc_info=False)
            return None, (
                "Hangi üniversite hakkında bilgi almak istediğinizi anlayamadım. "
                "Lütfen üniversite adını açıkça belirtin. "
                "Örnek: 'Marmara Üniversitesi öğrenci yönetmeliği nedir?'"
            )

        # Session'a bağla
        session.university_id = university.id
        db.commit()
        op.add_field("university_id", university.id).add_field("university_name", university.name)

        # 3. Crawl & embed
        if not university.is_crawled:
            await UniversityService._crawl_and_embed(university, db, op)
        else:
            await UniversityService._ensure_embedded(university, db, op)

        # 4. Belge kontrolü
        doc_count = db.query(Document).filter(Document.university_id == university.id).count()
        op.add_field("doc_count", doc_count)

        if doc_count == 0:
            op.fail(exc_info=False)
            return None, (
                f"{university.name} mevzuat sayfasına ulaşıldı ancak belge indirilemedi. "
                "Site geçici olarak erişime kapalı olabilir veya belgeler farklı bir formatta sunuluyor. "
                "Daha sonra tekrar deneyin."
            )

        op.succeed()
        return university, ""

    # ------------------------------------------------------------------
    # Dahili yardımcılar
    # ------------------------------------------------------------------

    @staticmethod
    async def _crawl_and_embed(university: University, db: Session, op) -> None:
        """Crawl yap; belge çıkmazsa URL keşfini çalıştır, sonra embed et."""
        crawler = UniversityCrawler()
        result = await crawler.crawl(university, db)
        docs_added = result.get("documents_added", 0)
        op.add_field("initial_crawl_docs", docs_added)

        if docs_added == 0:
            try:
                discovered_url = await discover_mevzuat_url(university.mevzuat_url)
            except Exception:
                logger.error(
                    {"event": "url_discovery_error", "university_id": university.id}
                )
                discovered_url = None

            if discovered_url and discovered_url != university.mevzuat_url:
                op.add_field("discovered_url", discovered_url)
                university.mevzuat_url = discovered_url
                university.is_crawled = False
                db.commit()
                result = await crawler.crawl(university, db)
                op.add_field("retry_crawl_docs", result.get("documents_added", 0))

        try:
            embed_university_documents(university.id, db)
        except Exception:
            logger.error({"event": "embed_failed", "university_id": university.id})

    @staticmethod
    async def _ensure_embedded(university: University, db: Session, op) -> None:
        """
        Üniversite daha önce crawl edilmişse Qdrant'ta chunk'ların
        varlığını kontrol eder; yoksa yeniden embed eder.
        """
        try:
            from qdrant_client import QdrantClient
            from app.core.config import settings

            qdrant = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
            existing = [c.name for c in qdrant.get_collections().collections]
            if COLLECTION_NAME not in existing:
                op.add_field("re_embed", True)
                embed_university_documents(university.id, db)
        except Exception:
            logger.error(
                {"event": "ensure_embedded_error", "university_id": university.id}
            )
            embed_university_documents(university.id, db)
