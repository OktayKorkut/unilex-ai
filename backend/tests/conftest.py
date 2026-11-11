"""
Test altyapısı.

Testler gerçek PostgreSQL, Qdrant ya da OpenAI'a bağlanmaz:
- Veritabanı: her test oturumu için geçici bir SQLite dosyası
- Qdrant ve OpenAI: ilgili testlerde sahte (fake) istemcilerle değiştirilir

Ortam değişkenleri `app` içe aktarılmadan ÖNCE ayarlanmalıdır, çünkü
`app.core.config.settings` ve veritabanı motoru içe aktarma anında oluşur.
"""

import os
import tempfile
from pathlib import Path

_DB_FILE = Path(tempfile.mkdtemp(prefix="unilex-test-")) / "test.db"

os.environ["DATABASE_URL"] = f"sqlite:///{_DB_FILE}"
os.environ["OPENAI_API_KEY"] = "test-openai-key"
os.environ["SECRET_KEY"] = "test-secret-key-only-for-tests"
os.environ["SMTP_USER"] = ""
os.environ["SMTP_PASSWORD"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def _clean_database():
    """Her testten önce tabloları sıfırlar; testler birbirini etkilemez."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture()
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client():
    # `with` kullanılmaz: lifespan (zamanlayıcı) testlerde başlatılmaz.
    return TestClient(app)


class FakeOpenAI:
    """`client.chat.completions.create(...)` çağrısını taklit eder ve parametreleri kaydeder."""

    def __init__(self, answer: str = "sahte yanıt"):
        self.answer = answer
        self.calls: list[dict] = []
        outer = self

        class _Message:
            def __init__(self, content):
                self.content = content

        class _Choice:
            def __init__(self, content):
                self.message = _Message(content)

        class _Response:
            def __init__(self, content):
                self.choices = [_Choice(content)]

        class _Completions:
            def create(self, **kwargs):
                outer.calls.append(kwargs)
                return _Response(outer.answer)

        class _Chat:
            completions = _Completions()

        self.chat = _Chat()


@pytest.fixture()
def fake_openai():
    return FakeOpenAI()
