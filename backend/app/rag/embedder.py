from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logger import get_logger
from app.db.models import Document

logger = get_logger("embedder")

COLLECTION_NAME = "documents"
VECTOR_SIZE = 1536   # text-embedding-3-small
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
MAX_CHUNK_CHARS = 15_000  # conservative limit; /uniXXXX-encoded PDFs tokenize at ~4x density

_openai_client: OpenAI | None = None
_qdrant_client: QdrantClient | None = None


def _get_openai() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai_client


def _get_qdrant() -> QdrantClient:
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
    return _qdrant_client


def _chunk_text(text: str) -> list[str]:
    words = text.split()
    chunks: list[str] = []
    start = 0
    while start < len(words):
        chunk = " ".join(words[start:start + CHUNK_SIZE])
        if chunk.strip():
            chunks.append(chunk[:MAX_CHUNK_CHARS])
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def _ensure_collection(client: QdrantClient) -> None:
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
        logger.info({"event": "collection_created", "collection": COLLECTION_NAME})


def embed_document(document: Document) -> None:
    """Belgeyi chunk'layıp Qdrant'a embed eder."""
    op = logger.start_operation("embed_document")
    op.add_field("document_id", document.id).add_field("title", document.title)

    try:
        openai_client = _get_openai()
        qdrant = _get_qdrant()

        _ensure_collection(qdrant)

        # Mevcut chunk'ları sil (yeniden embed durumunda temiz başla)
        qdrant.delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(
                must=[FieldCondition(key="document_id", match=MatchValue(value=document.id))]
            ),
        )

        chunks = _chunk_text(document.content)
        op.add_field("chunk_count", len(chunks))

        if not chunks:
            op.add_field("result", "empty_content").fail(exc_info=False)
            return

        batch_size = 50
        points: list[PointStruct] = []
        point_id_base = document.id * 100_000

        for batch_start in range(0, len(chunks), batch_size):
            batch = chunks[batch_start:batch_start + batch_size]
            response = openai_client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=batch,
            )
            for i, emb in enumerate(response.data):
                chunk_index = batch_start + i
                points.append(PointStruct(
                    id=point_id_base + chunk_index,
                    vector=emb.embedding,
                    payload={
                        "document_id": document.id,
                        "university_id": document.university_id,
                        "chunk_index": chunk_index,
                        "text": batch[i],
                        "title": document.title,
                        "source_url": document.source_url,
                    },
                ))

        qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
        op.add_field("points_upserted", len(points)).succeed()

    except Exception as e:
        op.fail()
        try:
            from app.db.database import SessionLocal
            from app.services.system_log_service import create_system_log
            with SessionLocal() as session:
                create_system_log(
                    session,
                    "error",
                    "Vektör DB Hatası",
                    f"{document.title} belgesi için vektör çıkarılırken hata oluştu: {str(e)[:250]}"
                )
        except Exception:
            pass
        raise


def embed_university_documents(university_id: int, db: Session) -> int:
    """Bir üniversitenin tüm belgelerini embed eder. Toplam chunk sayısını döner."""
    op = logger.start_operation("embed_university_documents")
    op.add_field("university_id", university_id)

    try:
        documents = db.query(Document).filter(Document.university_id == university_id).all()
        op.add_field("document_count", len(documents))

        total_chunks = 0
        failed = 0
        for doc in documents:
            try:
                embed_document(doc)
                total_chunks += len(_chunk_text(doc.content))
            except Exception:
                failed += 1
                logger.error({"event": "embed_document_skipped", "document_id": doc.id, "title": doc.title})

        op.add_field("total_chunks", total_chunks).add_field("failed_docs", failed).succeed()
        
        # Log successful embedding
        from app.services.system_log_service import create_system_log
        create_system_log(
            db,
            "info",
            "Model Embedding Güncellendi",
            f"{settings.LLM_MODEL} ({settings.EMBEDDING_MODEL}) ağırlıkları yenilendi. {total_chunks} adet vektör güncellendi."
        )
        
        return total_chunks

    except Exception:
        op.fail()
        raise
