# Unilex AI

Türk üniversitelerinin mevzuat belgelerini (yönetmelik, yönerge, statü vb.) otomatik toplayıp kullanıcı sorularını yapay zeka ile yanıtlayan agentic RAG sistemi.

## Ne Yapıyor?

Kullanıcı üniversite adını serbest yazıyla belirtebilir ya da listeden seçebilir. Agent şu adımları otomatik yürütür:

1. Mesajdan üniversite adını GPT ile tespit eder; DB'de yoksa kaydeder
2. Üniversitenin mevzuat sayfasını çok kademeli stratejyle bulur (URL pattern → sitemap → Playwright crawl)
3. Belgeleri PDF olarak indirir, metin çıkarır, PostgreSQL'e kaydeder
4. Metni 800 kelimelik chunk'lara böler, OpenAI ile embed eder, Qdrant'a yükler
5. Kullanıcı sorusu gelince ilgili chunk'ları vektör aramasıyla getirir, GPT-4o-mini ile yanıt üretir
6. Skor eşiğinin altındaysa soruya özel PDF bulup hedefli crawl başlatır ve yeniden yanıt dener

## Tech Stack

| Katman | Teknoloji |
|---|---|
| Backend | FastAPI (Python, async) |
| Crawler | Playwright + httpx |
| LLM | OpenAI gpt-4o-mini |
| Embeddings | OpenAI text-embedding-3-small |
| Vector DB | Qdrant (cosine similarity) |
| Database | PostgreSQL + SQLAlchemy |
| Auth | JWT (python-jose) |

## Proje Yapısı

```
unilex-ai/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routers/           # HTTP katmanı (auth, universities, chat, crawler, users, documents)
│   │   ├── core/
│   │   │   ├── config.py          # Pydantic BaseSettings, .env yükleme
│   │   │   ├── logger.py          # Structured JSON logging (UnilexLogger, OperationLog)
│   │   │   ├── exceptions.py      # Custom exception sınıfları ve global handler'lar
│   │   │   └── security.py        # JWT, bcrypt
│   │   ├── services/
│   │   │   ├── university_service.py   # Üniversite tespiti, crawl, embed orkestrasyonu
│   │   │   └── chat_service.py         # RAG pipeline, targeted search, mesaj kaydetme
│   │   ├── agent/
│   │   │   ├── chat_agent.py          # RAG + GPT yanıt üretimi
│   │   │   ├── university_detector.py # Mesajdan üniversite tespiti (GPT)
│   │   │   └── university_finder.py   # Yeni üniversite bilgisi üretimi (GPT)
│   │   ├── crawler/
│   │   │   ├── university_crawler.py  # Playwright ile mevzuat PDF crawl
│   │   │   ├── mevzuat_discovery.py   # Çok kademeli URL keşfi
│   │   │   └── targeted_crawler.py    # Soruya özel hedefli PDF crawl
│   │   ├── rag/
│   │   │   ├── embedder.py        # Chunk + OpenAI embed + Qdrant upsert
│   │   │   └── retriever.py       # Vektör arama ile chunk getirme
│   │   ├── db/
│   │   │   ├── models.py          # SQLAlchemy modelleri
│   │   │   ├── database.py        # Engine ve session
│   │   │   └── seed.py            # Başlangıç üniversite verisi
│   │   └── main.py                # Uygulama giriş noktası, exception handler kaydı
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── test.html                      # Tarayıcıdan test arayüzü
├── docker-compose.yml
└── README.md
```

## Geliştirme Fazları

| Faz | Konu | Durum |
|---|---|---|
| Faz 1 | Proje iskeleti, auth, Docker | ✅ Tamamlandı |
| Faz 2 | Playwright crawler, mevzuat PDF indirme | ✅ Tamamlandı |
| Faz 3 | RAG pipeline (chunk → embed → retrieve) | ✅ Tamamlandı |
| Faz 4 | Agentic chat (üniversite tespiti, URL keşfi, hedefli crawl) | ✅ Tamamlandı |
| Faz 5 | Kod kalitesi (logging, exception handling, service layer, async) | ✅ Tamamlandı |
| Faz 6 | Testler, ön yüz, dokümantasyon | 🔜 Sıradaki |

---

## Kurulum

### Gereksinimler

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Python 3.11+
- Git

### 1. Repoyu Klonla

```bash
git clone https://github.com/OktayKorkut/unilex-ai.git
cd unilex-ai
```

### 2. Environment Dosyasını Oluştur

```bash
cp backend/.env.example backend/.env
```

`backend/.env` dosyasını düzenle:

```env
OPENAI_API_KEY=sk-...
SECRET_KEY=...                # openssl rand -hex 32
DATABASE_URL=postgresql://unilex:unilex123@postgres:5432/unilex
QDRANT_HOST=qdrant
QDRANT_PORT=6333
```

### 3. Docker ile Başlat

```bash
docker compose up --build
```

| Servis | Adres |
|---|---|
| Backend API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |
| Qdrant Dashboard | http://localhost:6333/dashboard |

### 4. Sağlık Kontrolü

```bash
curl http://localhost:8000/health
```

```json
{"status":"ok","postgres":"connected","qdrant":"connected","app":"Unilex AI"}
```

---

## API Endpoints

### Auth

| Method | Endpoint | Açıklama |
|---|---|---|
| POST | `/api/v1/auth/register` | Yeni kullanıcı kaydı |
| POST | `/api/v1/auth/login` | Giriş — JWT token döner |

```bash
# Kayıt
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"123456","full_name":"Test User"}'

# Giriş
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"123456"}'
```

### Üniversiteler

| Method | Endpoint | Açıklama |
|---|---|---|
| GET | `/api/v1/universities/` | Tüm üniversiteleri listele |
| GET | `/api/v1/universities/{id}` | Üniversite detayı |

### Crawler

| Method | Endpoint | Açıklama |
|---|---|---|
| POST | `/api/v1/crawler/crawl/{university_id}` | Üniversiteyi crawl et ve embed et |

### Chat

| Method | Endpoint | Açıklama |
|---|---|---|
| POST | `/api/v1/chat/sessions` | Yeni sohbet başlat (`university_id` opsiyonel) |
| GET | `/api/v1/chat/sessions` | Sohbet listesi |
| GET | `/api/v1/chat/sessions/{id}` | Sohbet detayı (mesaj geçmişiyle) |
| POST | `/api/v1/chat/sessions/{id}/messages` | Mesaj gönder |
| DELETE | `/api/v1/chat/sessions/{id}` | Sohbeti sil |

```bash
TOKEN="Bearer <jwt_token>"

# Üniversite belirtmeden sohbet başlat
curl -X POST http://localhost:8000/api/v1/chat/sessions \
  -H "Authorization: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'

# Mesaj gönder — agent üniversiteyi mesajdan tespit eder
curl -X POST http://localhost:8000/api/v1/chat/sessions/1/messages \
  -H "Authorization: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"Marmara Üniversitesi öğrenci disiplin yönetmeliği nedir?"}'
```

---

## Mimari Notlar

### Agentic Akış

```
Mesaj geldi
  → university_id yoksa → GPT ile üniversite tespiti
    → DB'de yoksa → GPT ile bilgi üret + DB'ye kaydet
  → Crawl edilmemişse → Playwright ile crawl
    → 0 belge → çok kademeli URL keşfi → tekrar crawl
    → hâlâ 0 → "site erişilemiyor" mesajı
  → ask() → relevance skoru < 0.45
    → hedefli PDF arama → soruya özel crawl → retry ask()
    → hâlâ boş → anlamlı fallback mesajı
  → Yanıt dön
```

### Logging

Her modül `get_logger("modül_adı")` ile JSON logger alır. Her kritik işlem `start_operation()` → `add_field()` → `succeed()` / `fail()` döngüsüyle izlenir:

```json
{"timestamp":"2026-04-15T10:23:01.123Z","level":"INFO","logger":"unilex.chat_service",
 "operation_name":"answer_question","session_id":5,"university_id":3,
 "chunks_retrieved":5,"max_score":0.81,"answer_len":420,"status":"succeeded","duration_ms":1340}
```

### Error Handling

Tüm hatalar `UnilexException` subclass'larıyla yönetilir; global handler tutarlı JSON yanıt döner:

```json
{"error_code":"UNILEX_003","message":"Oturum bulunamadı veya bu oturuma erişim yetkiniz yok.","parameters":null}
```

| Kod | Sınıf | HTTP |
|---|---|---|
| UNILEX_001 | `UnilexException` (genel) | 500 |
| UNILEX_002 | `UniversityNotFoundError` | 404 |
| UNILEX_003 | `SessionNotFoundError` | 404 |
| UNILEX_004 | `CrawlFailedError` | 500 |
| UNILEX_005 | `EmbedFailedError` | 500 |
| UNILEX_006 | `ChatError` | 500 |
| UNILEX_007 | Validation hatası | 422 |
| UNILEX_008 | Üniversite tespit hatası | 400 |
