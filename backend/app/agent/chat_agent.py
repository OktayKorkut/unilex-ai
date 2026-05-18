from app.core.logger import get_logger
from app.rag.retriever import retrieve
from app.rag.embedder import _get_openai
from app.core.config import settings

logger = get_logger("chat_agent")

SYSTEM_PROMPT = """Sen Unilex AI'sın. Türk üniversitelerinin mevzuat belgelerini (yönetmelik, yönerge, statü vb.) analiz eden bir yapay zeka asistanısın.

Görevin:
- Kullanıcının sorularını yalnızca sağlanan bağlam belgelerine dayanarak yanıtlamak
- Yanıtlarını Türkçe vermek
- Eğer bağlamda yeterli bilgi yoksa bunu açıkça belirtmek
- Madde numaralarına, yönetmelik adlarına atıfta bulunmak

Önemli: Bağlamda olmayan bilgileri uydurmak kesinlikle yasak."""

RELEVANCE_THRESHOLD = 0.45


def _build_context(chunks: list[dict]) -> str:
    parts = [f"[Kaynak {i}: {c['title']}]\n{c['text']}" for i, c in enumerate(chunks, 1)]
    return "\n\n---\n\n".join(parts)


def ask(
    question: str,
    university_id: int,
    history: list[dict],
) -> tuple[str, list[dict], bool]:
    """
    Soruyu RAG pipeline'ı aracılığıyla yanıtlar.

    Returns:
        (answer, sources, needs_targeted_search)
        needs_targeted_search=True ise caller hedefli PDF araması başlatmalı.
    """
    op = logger.start_operation("ask")
    op.add_field("university_id", university_id).add_field("question_len", len(question))

    chunks = retrieve(query=question, university_id=university_id, top_k=5)
    op.add_field("chunks_retrieved", len(chunks))

    if not chunks:
        op.add_field("result", "no_chunks").fail(exc_info=False)
        return (
            "Bu üniversiteye ait mevzuat belgelerinde sorunuzu yanıtlayacak içerik bulunamadı.",
            [],
            True,
        )

    max_score = max(c["score"] for c in chunks)
    op.add_field("max_score", max_score)

    if max_score < RELEVANCE_THRESHOLD:
        op.add_field("result", "low_relevance").debug()
        return "", chunks, True

    context = _build_context(chunks)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += history[-6:]
    messages.append({
        "role": "user",
        "content": f"Bağlam Belgeler:\n\n{context}\n\nSoru: {question}",
    })

    try:
        response = _get_openai().chat.completions.create(
            model=settings.LLM_MODEL,
            messages=messages,
            temperature=0.2,
            max_tokens=1024,
        )
        answer = response.choices[0].message.content
        op.add_field("answer_len", len(answer)).succeed()
        return answer, chunks, False
    except Exception:
        op.fail()
        raise
