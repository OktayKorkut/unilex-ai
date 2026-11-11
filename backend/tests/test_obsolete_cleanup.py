"""
Eskiyen belge temizliği ve %80 güvenlik eşiği.

Hatalı bir crawl (ör. site geçici olarak boş döndü) tüm bilgi tabanını
silmemelidir; bu testler o korumayı doğrular.
"""

import pytest

from app.db.models import Document, SystemLog, University
from app.services import crawl_job_service
from app.services.crawl_job_service import _remove_obsolete_documents


class FakeQdrant:
    def __init__(self, fail: bool = False):
        self.deleted = []
        self.fail = fail

    def delete(self, collection_name, points_selector):
        if self.fail:
            raise RuntimeError("qdrant down")
        self.deleted.append(points_selector)


@pytest.fixture()
def qdrant(monkeypatch):
    fake = FakeQdrant()
    monkeypatch.setattr(crawl_job_service, "_get_qdrant", lambda: fake)
    return fake


def _university(db, slug="isik") -> University:
    uni = University(name=f"Üniversite {slug}", slug=slug, mevzuat_url="https://ornek.edu.tr")
    db.add(uni)
    db.commit()
    return uni


def _documents(db, uni, count, prefix="d") -> list[str]:
    urls = []
    for i in range(count):
        url = f"https://ornek.edu.tr/{prefix}{i}.pdf"
        db.add(Document(university_id=uni.id, title=f"Belge {i}", content="metin", source_url=url))
        urls.append(url)
    db.commit()
    return urls


def _remaining(db, uni) -> int:
    return db.query(Document).filter(Document.university_id == uni.id).count()


def test_nothing_is_removed_when_all_documents_are_still_fresh(db, qdrant):
    uni = _university(db)
    urls = _documents(db, uni, 5)

    assert _remove_obsolete_documents(db, uni.id, set(urls)) == 0
    assert _remaining(db, uni) == 5
    assert qdrant.deleted == []


def test_obsolete_documents_are_removed_from_db_and_vector_store(db, qdrant):
    uni = _university(db)
    urls = _documents(db, uni, 5)

    removed = _remove_obsolete_documents(db, uni.id, set(urls[1:]))  # ilki artık yok

    assert removed == 1
    assert _remaining(db, uni) == 4
    assert len(qdrant.deleted) == 1


def test_exactly_80_percent_is_still_allowed(db, qdrant):
    uni = _university(db)
    urls = _documents(db, uni, 5)

    removed = _remove_obsolete_documents(db, uni.id, {urls[0]})  # 4/5 = %80, eşik "aşılırsa" iptal

    assert removed == 4
    assert _remaining(db, uni) == 1


def test_cleanup_is_aborted_just_above_the_threshold(db, qdrant):
    uni = _university(db)
    urls = _documents(db, uni, 10)

    removed = _remove_obsolete_documents(db, uni.id, {urls[0]})  # 9/10 = %90 > %80

    assert removed == 0
    assert _remaining(db, uni) == 10


def test_cleanup_is_aborted_above_80_percent_and_a_warning_is_logged(db, qdrant):
    uni = _university(db)
    _documents(db, uni, 5)

    removed = _remove_obsolete_documents(db, uni.id, fresh_urls=set())  # 5/5 = %100

    assert removed == 0
    assert _remaining(db, uni) == 5  # hiçbir belge silinmedi
    assert qdrant.deleted == []
    log = db.query(SystemLog).one()
    assert log.level == "warning"
    assert log.title == "Obsolete Cleanup İptal"
    assert "5/5" in log.message


def test_other_universities_are_never_touched(db, qdrant):
    isik = _university(db, "isik")
    baska = _university(db, "baska")
    isik_urls = _documents(db, isik, 5, prefix="isik")
    _documents(db, baska, 3, prefix="baska")

    _remove_obsolete_documents(db, isik.id, set(isik_urls[1:]))

    assert _remaining(db, baska) == 3


def test_vector_store_failure_does_not_block_database_cleanup(db, monkeypatch):
    monkeypatch.setattr(crawl_job_service, "_get_qdrant", lambda: FakeQdrant(fail=True))
    uni = _university(db)
    urls = _documents(db, uni, 5)

    removed = _remove_obsolete_documents(db, uni.id, set(urls[1:]))

    assert removed == 1
    assert _remaining(db, uni) == 4
