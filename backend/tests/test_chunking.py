from app.rag.embedder import CHUNK_OVERLAP, CHUNK_SIZE, MAX_CHUNK_CHARS, _chunk_text


def _words(n: int) -> str:
    return " ".join(f"w{i}" for i in range(n))


def test_empty_and_whitespace_produce_no_chunks():
    assert _chunk_text("") == []
    assert _chunk_text("   \n\t  ") == []


def test_short_text_is_a_single_chunk():
    chunks = _chunk_text(_words(10))
    assert len(chunks) == 1
    assert chunks[0] == _words(10)


def test_text_exactly_one_chunk_long_is_not_split_twice():
    # 800 kelime: ilk chunk her şeyi kapsar, ikinci chunk yalnızca örtüşen kuyruk olur
    chunks = _chunk_text(_words(CHUNK_SIZE))
    assert len(chunks[0].split()) == CHUNK_SIZE


def test_long_text_is_split_with_configured_size():
    chunks = _chunk_text(_words(2000))
    assert len(chunks[0].split()) == CHUNK_SIZE
    assert all(len(c.split()) <= CHUNK_SIZE for c in chunks)


def test_consecutive_chunks_overlap_by_configured_amount():
    chunks = _chunk_text(_words(2000))
    first_tail = chunks[0].split()[-CHUNK_OVERLAP:]
    second_head = chunks[1].split()[:CHUNK_OVERLAP]
    assert first_tail == second_head


def test_every_word_is_covered_by_at_least_one_chunk():
    total = 2500
    seen = set()
    for chunk in _chunk_text(_words(total)):
        seen.update(chunk.split())
    assert seen == {f"w{i}" for i in range(total)}


def test_chunk_is_truncated_to_max_characters():
    # Çok uzun "kelimeler" (bozuk PDF kodlaması gibi) karakter sınırını aşmamalı
    huge = " ".join("x" * 100 for _ in range(CHUNK_SIZE))
    assert len(huge) > MAX_CHUNK_CHARS
    chunks = _chunk_text(huge)
    assert all(len(c) <= MAX_CHUNK_CHARS for c in chunks)
