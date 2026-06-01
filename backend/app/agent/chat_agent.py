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

SMALLTALK_SYSTEM = (
    "Sen Unilex AI'sın, Türk üniversitelerinin mevzuat belgelerini analiz eden bir asistansın. "
    "Kullanıcı sana günlük bir mesaj gönderiyor. Kısa ve samimi bir şekilde yanıt ver. "
    "Üniversite mevzuatı hakkında soru sormaya davet et."
)

_SMALLTALK_KEYWORDS = frozenset({
    "merhaba", "selam", "selamlar", "hey", "hi", "hello", "iyi günler",
    "iyi akşamlar", "iyi geceler", "günaydın",
    "nasılsın", "nasılsınız", "iyi misin", "ne haber", "naber", "ne var ne yok",
    "teşekkür", "teşekkürler", "teşekkür ederim", "sağ ol", "sağ olun", "eyvallah",
    "görüşürüz", "hoşçakal", "hoşça kal", "güle güle", "bay bay", "kendine iyi bak",
    "tamam", "peki", "anladım", "harika", "süper",
})

_MEVZUAT_KEYWORDS = frozenset({
    "yönetmelik", "yönerge", "statü", "madde", "fıkra", "burs", "staj",
    "başvuru", "kayıt", "not", "puan", "mezun", "diploma", "lisans", "yüksek lisans",
    "doktora", "çap", "yandal", "muafiyet", "sınav", "ödev", "disiplin",
})


def _is_smalltalk(question: str) -> bool:
    q = question.lower().strip()
    words = set(q.split())
    has_smalltalk = bool(words & _SMALLTALK_KEYWORDS)
    has_mevzuat = any(kw in q for kw in _MEVZUAT_KEYWORDS)
    return has_smalltalk and not has_mevzuat


RELEVANCE_THRESHOLD = 0.60


def _build_context(chunks: list[dict]) -> str:
    parts = [f"[Kaynak {i}: {c['title']}]\n{c['text']}" for i, c in enumerate(chunks, 1)]
    return "\n\n---\n\n".join(parts)


def ask(
    question: str,
    university_id: int,
    history: list[dict],
    threshold: float = RELEVANCE_THRESHOLD,
) -> tuple[str, list[dict], bool]:
    """
    Soruyu RAG pipeline'ı aracılığıyla yanıtlar.

    Returns:
        (answer, sources, needs_targeted_search)
        needs_targeted_search=True ise caller hedefli PDF araması başlatmalı.
    """
    op = logger.start_operation("ask")
    op.add_field("university_id", university_id).add_field("question_len", len(question))

    if _is_smalltalk(question):
        op.add_field("result", "smalltalk").succeed()
        messages = [{"role": "system", "content": SMALLTALK_SYSTEM}]
        messages += history[-4:]
        messages.append({"role": "user", "content": question})
        response = _get_openai().chat.completions.create(
            model=settings.LLM_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=150,
        )
        return response.choices[0].message.content, [], False

    all_chunks = retrieve(query=question, university_id=university_id, top_k=10)
    op.add_field("chunks_retrieved", len(all_chunks))

    if not all_chunks:
        op.add_field("result", "no_chunks").fail(exc_info=False)
        return (
            "Bu üniversiteye ait mevzuat belgelerinde sorunuzu yanıtlayacak içerik bulunamadı.",
            [],
            True,
        )

    # Filter chunks by threshold
    chunks = [c for c in all_chunks if c["score"] >= threshold]

    if not chunks:
        max_score = max(c["score"] for c in all_chunks)
        op.add_field("max_score", max_score)
        op.add_field("result", "low_relevance").debug()
        return "", all_chunks[:5], True

    max_score = max(c["score"] for c in chunks)
    op.add_field("max_score", max_score)

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
