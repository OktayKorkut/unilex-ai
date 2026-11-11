import pytest

from app.agent import chat_agent
from app.agent.chat_agent import RELEVANCE_THRESHOLD, ask, is_smalltalk


def _chunk(text: str, score: float, title: str = "Yönetmelik") -> dict:
    return {"text": text, "title": title, "source_url": "https://ornek.edu.tr/a.pdf", "score": score}


@pytest.fixture()
def patched(monkeypatch, fake_openai):
    """retrieve() ve OpenAI istemcisini sahteleriyle değiştirir."""
    state = {"chunks": [], "retrieve_calls": []}

    def fake_retrieve(query, university_id, top_k=5):
        state["retrieve_calls"].append({"query": query, "university_id": university_id, "top_k": top_k})
        return state["chunks"]

    monkeypatch.setattr(chat_agent, "retrieve", fake_retrieve)
    monkeypatch.setattr(chat_agent, "_get_openai", lambda: fake_openai)
    state["openai"] = fake_openai
    return state


class TestSmalltalkDetection:
    @pytest.mark.parametrize("text", ["merhaba", "Selam", "teşekkür ederim", "günaydın", "nasılsın"])
    def test_greetings_are_smalltalk(self, text):
        assert is_smalltalk(text) is True

    @pytest.mark.parametrize(
        "text",
        [
            "Çift anadal başvurusu için GNO şartı nedir?",
            "Merhaba, burs başvurusu nasıl yapılır?",  # selamlaşma + mevzuat sorusu
            "staj süresi kaç gün",
            "",
        ],
    )
    def test_real_questions_are_not_smalltalk(self, text):
        assert is_smalltalk(text) is False


class TestAsk:
    def test_smalltalk_skips_retrieval(self, patched):
        answer, sources, needs_search = ask("merhaba", university_id=1, history=[])
        assert patched["retrieve_calls"] == []
        assert sources == []
        assert needs_search is False
        assert answer == "sahte yanıt"

    def test_no_chunks_requests_targeted_search(self, patched):
        patched["chunks"] = []
        answer, sources, needs_search = ask("Çift anadal şartı nedir?", 1, [])
        assert needs_search is True
        assert sources == []
        assert patched["openai"].calls == []  # model çağrılmaz
        assert "bulunamadı" in answer

    def test_low_relevance_requests_targeted_search_without_calling_llm(self, patched):
        patched["chunks"] = [_chunk("alakasız", 0.30), _chunk("yine alakasız", 0.20)]
        answer, sources, needs_search = ask("Çift anadal şartı nedir?", 1, [])
        assert needs_search is True
        assert answer == ""
        assert len(sources) == 2
        assert patched["openai"].calls == []

    def test_only_chunks_above_threshold_are_used_as_context_and_sources(self, patched):
        patched["chunks"] = [
            _chunk("ALAKALI-BIR", 0.91),
            _chunk("ALAKALI-IKI", 0.72),
            _chunk("ALAKASIZ", 0.40),
        ]
        answer, sources, needs_search = ask("Çift anadal şartı nedir?", 1, [])

        assert needs_search is False
        assert answer == "sahte yanıt"
        assert [s["text"] for s in sources] == ["ALAKALI-BIR", "ALAKALI-IKI"]

        sent = patched["openai"].calls[0]["messages"]
        user_prompt = sent[-1]["content"]
        assert "ALAKALI-BIR" in user_prompt and "ALAKALI-IKI" in user_prompt
        assert "ALAKASIZ" not in user_prompt

    def test_chunk_exactly_at_threshold_is_included(self, patched):
        patched["chunks"] = [_chunk("SINIRDA", RELEVANCE_THRESHOLD)]
        _, sources, needs_search = ask("Çift anadal şartı nedir?", 1, [])
        assert needs_search is False
        assert [s["text"] for s in sources] == ["SINIRDA"]

    def test_retrieval_is_scoped_to_the_given_university(self, patched):
        patched["chunks"] = [_chunk("x", 0.9)]
        ask("Çift anadal şartı nedir?", university_id=7, history=[])
        assert patched["retrieve_calls"][0]["university_id"] == 7

    def test_only_recent_history_is_sent_to_the_model(self, patched):
        patched["chunks"] = [_chunk("x", 0.9)]
        history = [{"role": "user", "content": f"mesaj-{i}"} for i in range(10)]
        ask("Çift anadal şartı nedir?", 1, history)

        sent = patched["openai"].calls[0]["messages"]
        # 1 sistem + son 6 geçmiş mesajı + 1 kullanıcı sorusu
        assert len(sent) == 8
        assert sent[0]["role"] == "system"
        assert sent[1]["content"] == "mesaj-4"

    def test_system_prompt_forbids_making_things_up(self, patched):
        patched["chunks"] = [_chunk("x", 0.9)]
        ask("Çift anadal şartı nedir?", 1, [])
        system = patched["openai"].calls[0]["messages"][0]["content"]
        assert "uydurmak kesinlikle yasak" in system

    def test_llm_failure_is_propagated_not_swallowed(self, patched, monkeypatch):
        patched["chunks"] = [_chunk("x", 0.9)]

        class Boom:
            class chat:
                class completions:
                    @staticmethod
                    def create(**_):
                        raise RuntimeError("openai down")

        monkeypatch.setattr(chat_agent, "_get_openai", lambda: Boom)
        with pytest.raises(RuntimeError):
            ask("Çift anadal şartı nedir?", 1, [])
