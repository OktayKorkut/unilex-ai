"""
Unilex AI — sohbet iş mantığı servisi.

RAG pipeline çağrısını, hedefli PDF aramasını ve mesaj kaydetmeyi
router'dan ayırır.
"""

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logger import get_logger
from app.db.models import ChatSession, Message, University
from app.agent.chat_agent import ask
from app.crawler.targeted_crawler import search_and_embed_for_question
from app.rag.embedder import _get_openai

logger = get_logger("chat_service")

def _build_fallback_message(university: University | None) -> str:
    base = (
        "Bu soruya yanıt verecek ilgili bir belge bulunamadı. "
        "Üniversitenin mevzuat sayfasında bu konuyla ilgili bir PDF tespit edilemedi. "
        "Soruyu farklı bir şekilde sorabilir veya daha spesifik bir konu belirtebilirsiniz."
    )
    if university and university.mevzuat_url:
        base += f"\n\nResmi mevzuat sayfasından manuel arama yapmak için: {university.mevzuat_url}"
    return base


class ChatService:

    @staticmethod
    async def answer_question(
        session: ChatSession,
        content: str,
        db: Session,
        history: list[dict] | None = None,
    ) -> tuple[str, list[dict]]:
        """
        Soruyu RAG pipeline'ına iletir.

        Relevance skoru düşükse hedefli PDF araması başlatır ve yeniden dener.
        Her durumda anlamlı bir yanıt döner — boş string asla dönmez.

        Returns:
            (answer, sources)
        """
        op = logger.start_operation("answer_question")
        op.add_field("session_id", session.id).add_field("university_id", session.university_id)

        if history is None:
            history = [{"role": m.role, "content": m.content} for m in session.messages]

        answer, sources, needs_targeted_search = ask(
            question=content,
            university_id=session.university_id,
            history=history,
        )
        no_info_keywords = [
            "bilgi bulunmamaktadır",
            "bilgi yok",
            "yeterli bilgi yok",
            "tespit edilemedi",
            "mevcut değildir",
            "bilgi bulunamadı",
            "bilgi mevcut değil",
            "bulunamamıştır"
        ]
        has_no_info = any(kw in answer.lower() for kw in no_info_keywords) if answer else True
        op.add_field("needs_targeted_search", needs_targeted_search)
        op.add_field("has_no_info", has_no_info)
        op.add_field("initial_sources", len(sources))

        university: University | None = None
        if needs_targeted_search or has_no_info:
            university = db.query(University).filter(
                University.id == session.university_id
            ).first()

            added = 0
            if university:
                try:
                    added = await search_and_embed_for_question(content, university, db)
                    op.add_field("targeted_docs_added", added)
                    if added > 0:
                        answer, sources, _ = ask(
                            question=content,
                            university_id=session.university_id,
                            history=history,
                        )
                except Exception:
                    logger.error(
                        {"event": "targeted_search_failed", "university_id": university.id}
                    )

            if not answer or (any(kw in answer.lower() for kw in no_info_keywords) and not added):
                fallback_answer, fallback_sources, _ = ask(
                    question=content,
                    university_id=session.university_id,
                    history=history,
                    threshold=0.35,
                )
                if fallback_answer and not any(kw in fallback_answer.lower() for kw in no_info_keywords):
                    answer = fallback_answer
                    sources = fallback_sources
                else:
                    answer = _build_fallback_message(university)
                    sources = []

        op.add_field("answer_length", len(answer)).succeed()
        return answer, sources

    @staticmethod
    def generate_title(question: str) -> str:
        """İlk kullanıcı sorusundan GPT ile kısa sohbet başlığı üretir."""
        try:
            response = _get_openai().chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Kullanıcının sorusunu en fazla 6 kelimelik kısa bir başlığa dönüştür. "
                            "Yalnızca başlığı yaz, başka hiçbir şey ekleme."
                        ),
                    },
                    {"role": "user", "content": question},
                ],
                max_tokens=20,
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()[:120]
        except Exception:
            return question[:80]

    @staticmethod
    def save_messages(session_id: int, question: str, answer: str, db: Session, sources: list[dict] | None = None) -> Message:
        """Kullanıcı sorusunu ve asistan yanıtını DB'ye kaydeder ve asistan mesajını döner."""
        user_msg = Message(session_id=session_id, role="user", content=question)
        assistant_msg = Message(session_id=session_id, role="assistant", content=answer, sources=sources)
        db.add(user_msg)
        db.add(assistant_msg)
        db.commit()
        db.refresh(assistant_msg)
        return assistant_msg

    @staticmethod
    def save_assistant_message(session_id: int, answer: str, db: Session, sources: list[dict] | None = None) -> Message:
        """Sadece asistan mesajını DB'ye kaydeder. Regeneration için kullanılır."""
        assistant_msg = Message(session_id=session_id, role="assistant", content=answer, sources=sources)
        db.add(assistant_msg)
        db.commit()
        db.refresh(assistant_msg)
        return assistant_msg
