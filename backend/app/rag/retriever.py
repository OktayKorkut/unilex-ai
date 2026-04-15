from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.core.config import settings
from app.core.logger import get_logger
from app.rag.embedder import COLLECTION_NAME

logger = get_logger("retriever")


def retrieve(query: str, university_id: int, top_k: int = 5) -> list[dict]:
    """
    Kullanıcı sorusunu embed edip Qdrant'ta en yakın chunk'ları döner.

    Returns:
        [{"text": ..., "title": ..., "source_url": ..., "score": ...}]
    """
    op = logger.start_operation("retrieve")
    op.add_field("university_id", university_id).add_field("top_k", top_k)

    try:
        openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        qdrant = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)

        response = openai_client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=query,
        )
        query_vector = response.data[0].embedding

        # Collection yoksa boş dön
        existing = [c.name for c in qdrant.get_collections().collections]
        if COLLECTION_NAME not in existing:
            op.add_field("result", "collection_missing").fail(exc_info=False)
            return []

        results = qdrant.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            query_filter=Filter(
                must=[FieldCondition(key="university_id", match=MatchValue(value=university_id))]
            ),
            limit=top_k,
            with_payload=True,
        )

        chunks = [
            {
                "text": r.payload["text"],
                "title": r.payload.get("title", ""),
                "source_url": r.payload.get("source_url", ""),
                "score": r.score,
            }
            for r in results
        ]
        op.add_field("chunks_found", len(chunks)).succeed()
        return chunks

    except Exception:
        op.fail()
        return []
