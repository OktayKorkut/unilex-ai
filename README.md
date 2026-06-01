# Unilex AI

Türk üniversitelerinin mevzuat belgelerini (yönetmelik, yönerge, statü vb.) otomatik toplayıp kullanıcı sorularını yapay zeka ile yanıtlayan agentic RAG sistemi.

## Ne Yapıyor?

Kullanıcı üniversite adını serbest yazıyla belirtebilir ya da listeden seçebilir. Sistem şu adımları otomatik yürütür:

1. Mesajdan üniversite adını GPT ile tespit eder; DB'de yoksa kaydeder
2. Üniversitenin mevzuat sayfasını çok kademeli stratejiyle bulur (URL pattern → sitemap → Playwright crawl)
3. Belgeleri PDF olarak indirir, metin çıkarır, PostgreSQL'e kaydeder
4. Metni 800 kelimelik chunk'lara böler, OpenAI ile embed eder, Qdrant'a yükler
5. Kullanıcı sorusu gelince ilgili chunk'ları vektör aramasıyla getirir, GPT-4o-mini ile yanıt üretir
6. Skor eşiğinin altındaysa soruya özel PDF bulup hedefli crawl başlatır ve yeniden yanıt dener
7. Yanıt bulunamazsa üniversitenin resmi mevzuat sayfasına bağlantı verir
8. Admin re-crawl tetiklendiğinde vektör DB'den eskimiş belgeler otomatik temizlenir
9. APScheduler ile her 24 saatte bir tüm üniversiteleri otomatik yeniden crawl eder

## Tech Stack

| Katman | Teknoloji |
|---|---|
| Backend | FastAPI 0.115 (Python, async) |
| Frontend | React 19 + Vite + Mantine UI v9 |
| Crawler | Playwright + httpx |
| LLM | OpenAI gpt-4o-mini |
| Embeddings | OpenAI text-embedding-3-small (1536 dim) |
| Vector DB | Qdrant (cosine similarity) |
| Database | PostgreSQL 16 + SQLAlchemy 2.0 |
| Migrations | Alembic |
| Scheduler | APScheduler (AsyncIOScheduler) |
| Auth | JWT (python-jose) + bcrypt |
| Email | fastapi-mail (SMTP — şifre sıfırlama) |
| Web Server | Nginx (frontend container) |

## Proje Yapısı

```
unilex-ai/
├── backend/
│   ├── alembic/versions/
│   │   ├── 0001_initial_schema.py
│   │   ├── 0002_add_is_admin_to_users.py
│   │   ├── 0003_add_user_profile_and_session_title.py
│   │   ├── 0004_add_sources_to_messages.py
│   │   ├── 0005_add_message_id_to_feedback.py
│   │   └── 0006_extend_feedback_and_add_system_logs.py
│   ├── app/
│   │   ├── api/routers/
│   │   │   ├── auth.py            # Kayıt, giriş, şifre sıfırlama
│   │   │   ├── users.py           # Profil, avatar, KVKK hesap silme
│   │   │   ├── universities.py    # Üniversite CRUD
│   │   │   ├── crawler.py         # Crawl tetikleme (202 async), durum, embed
│   │   │   ├── documents.py       # Belge listeleme ve PDF yükleme
│   │   │   ├── chat.py            # Sohbet oturumları, mesajlaşma, regeneration
│   │   │   ├── feedback.py        # İletişim formu ve chat geri bildirimleri
│   │   │   └── admin.py           # Admin: istatistik, kullanıcı/belge yönetimi, loglar
│   │   ├── core/
│   │   │   ├── config.py          # Pydantic BaseSettings, .env yükleme
│   │   │   ├── logger.py          # Structured JSON logging
│   │   │   ├── exceptions.py      # Custom exception sınıfları ve global handler'lar
│   │   │   ├── security.py        # JWT, bcrypt, reset token
│   │   │   └── scheduler.py       # APScheduler periyodik crawl görevi
│   │   ├── services/
│   │   │   ├── university_service.py   # Üniversite tespiti, embed orkestrasyonu
│   │   │   ├── chat_service.py         # RAG pipeline, targeted search, fallback
│   │   │   ├── crawl_job_service.py    # Arka plan crawl + obsolete cleanup
│   │   │   ├── email_service.py        # SMTP ile şifre sıfırlama e-postası
│   │   │   └── system_log_service.py   # Sistem log yazma ve okuma
│   │   ├── agent/
│   │   │   ├── chat_agent.py           # RAG + GPT yanıt üretimi, smalltalk tespiti
│   │   │   ├── university_detector.py  # Mesajdan üniversite tespiti (GPT)
│   │   │   └── university_finder.py    # Yeni üniversite bilgisi üretimi (GPT)
│   │   ├── crawler/
│   │   │   ├── university_crawler.py   # Playwright ile mevzuat PDF crawl
│   │   │   ├── mevzuat_discovery.py    # Çok kademeli URL keşfi
│   │   │   └── targeted_crawler.py     # Soruya özel hedefli PDF crawl
│   │   ├── rag/
│   │   │   ├── embedder.py             # Chunk + OpenAI embed + Qdrant upsert
│   │   │   └── retriever.py            # Vektör arama ile chunk getirme
│   │   ├── db/
│   │   │   ├── models.py              # SQLAlchemy modelleri
│   │   │   ├── database.py            # Engine ve session
│   │   │   └── universities.json      # Seed verisi
│   │   └── main.py                    # Uygulama giriş noktası, lifespan, router kaydı
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── HomePage/
│   │   │   ├── ChatPage/
│   │   │   ├── ProfilePage/
│   │   │   ├── AboutPage/
│   │   │   ├── ContactPage/
│   │   │   ├── ResetPasswordPage/
│   │   │   ├── AdminPage/
│   │   │   ├── AdminCrawlerPage/
│   │   │   └── AdminHealthPage/
│   │   └── components/
│   │       ├── AuthModal/        # Giriş, kayıt, şifremi unuttum
│   │       ├── ChatMessage/      # Mesaj balonu, kaynak paneli, feedback
│   │       └── AdminSidebar/
│   ├── Dockerfile                # Multi-stage: node build → nginx serve
│   └── nginx.conf                # SPA fallback, gzip, cache headers
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
| Faz 5 | Kod kalitesi (logging, exception handling, service layer) | ✅ Tamamlandı |
| Faz 6 | Alembic migration, admin paneli, KVKK, periyodik crawl | ✅ Tamamlandı |
| Faz 7 | React frontend (chat, profil, admin dashboard, sistem yükü grafiği) | ✅ Tamamlandı |
| Faz 8 | RAD/SDD gereksinimleri: şifre sıfırlama, fallback linki, obsolete cleanup, pagination, Nginx container | ✅ Tamamlandı |

---

## Kurulum

### Gereksinimler

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
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
# Veritabanı
DATABASE_URL=postgresql://unilex:unilex123@postgres:5432/unilex

# Qdrant
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# OpenAI
OPENAI_API_KEY=sk-...

# JWT
SECRET_KEY=...              # openssl rand -hex 32

# SMTP — şifre sıfırlama e-postası (Gmail App Password önerilir)
SMTP_HOST=smtp.gmail.com
SMTP_USER=ornek@gmail.com
SMTP_PASSWORD=<app-password>
SMTP_FROM=ornek@gmail.com
FRONTEND_URL=http://localhost:3000

# Opsiyonel
CRAWL_INTERVAL_HOURS=24
```

> **Gmail App Password:** [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) adresinden oluşturulur. SMTP ayarları boş bırakılırsa şifre sıfırlama token'ı backend loguna yazılır (geliştirme modu).

### 3. Docker ile Başlat

```bash
docker compose up --build
```

Uygulama başlarken `alembic upgrade head` otomatik çalışır — migration'lar uygulanır.

| Servis | Adres |
|---|---|
| Frontend | http://localhost:3000 |
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
| POST | `/api/v1/auth/forgot-password` | Şifre sıfırlama e-postası gönderir (her zaman 200) |
| POST | `/api/v1/auth/reset-password` | Token + yeni şifre ile şifre günceller |

### Kullanıcı

| Method | Endpoint | Açıklama |
|---|---|---|
| GET | `/api/v1/users/me` | Profil bilgisi |
| PUT | `/api/v1/users/me` | Üniversite / ayarlar güncelle |
| POST | `/api/v1/users/me/avatar` | Profil fotoğrafı yükle |
| DELETE | `/api/v1/users/me` | Hesabı ve tüm kişisel veriyi sil (KVKK) |

### Üniversiteler

| Method | Endpoint | Açıklama |
|---|---|---|
| GET | `/api/v1/universities/` | Tüm üniversiteleri listele |
| GET | `/api/v1/universities/{id}` | Üniversite detayı |
| POST | `/api/v1/universities/` | Yeni üniversite ekle |
| POST | `/api/v1/universities/{id}/crawl` | Crawl başlat — 202 Accepted, arka planda çalışır; eskimiş belgeler otomatik temizlenir |
| GET | `/api/v1/universities/{id}/crawl-status` | Crawl durumu ve belge istatistiği |
| POST | `/api/v1/universities/{id}/embed` | Mevcut belgeleri Qdrant'a yeniden embed et |

### Belgeler

| Method | Endpoint | Açıklama |
|---|---|---|
| GET | `/api/v1/universities/{id}/documents` | Üniversite belgeleri |
| GET | `/api/v1/documents/{id}` | Belge detayı |
| POST | `/api/v1/universities/{id}/upload-pdf` | PDF yükle + embed (admin) |

### Chat

| Method | Endpoint | Açıklama |
|---|---|---|
| POST | `/api/v1/chat/sessions` | Yeni sohbet başlat |
| GET | `/api/v1/chat/sessions` | Sohbet listesi |
| POST | `/api/v1/chat/sessions/{id}/messages` | Mesaj gönder — `answer` + `sources` döner |
| DELETE | `/api/v1/chat/sessions/{id}` | Sohbeti sil |
| POST | `/api/v1/chat/sessions/{id}/messages/{msg_id}/regenerate` | Yanıtı yeniden üret |

### Geri Bildirim

| Method | Endpoint | Açıklama |
|---|---|---|
| POST | `/api/v1/feedbacks` | İletişim formu gönder |
| POST | `/api/v1/feedbacks/chat-feedback` | Chat mesajını değerlendir (👍/👎) |
| DELETE | `/api/v1/feedbacks/chat-feedback/{id}` | Değerlendirme sil |

### Admin *(is_admin gerektirir)*

| Method | Endpoint | Açıklama |
|---|---|---|
| GET | `/api/v1/admin/stats` | Sistem istatistikleri |
| GET | `/api/v1/admin/users` | Kullanıcı listesi (sayfalı) |
| DELETE | `/api/v1/admin/users/{id}` | Kullanıcıyı ve verilerini sil |
| PATCH | `/api/v1/admin/users/{id}/promote` | Kullanıcıyı admin yap |
| GET | `/api/v1/admin/documents` | Belgeleri listele — `?university_id=` + sayfalı |
| DELETE | `/api/v1/admin/documents/{id}` | Belgeyi DB + Qdrant'tan sil |
| GET | `/api/v1/admin/feedbacks` | İletişim formu geri bildirimleri (sayfalı) |
| GET | `/api/v1/admin/bad-feedbacks` | Olumsuz değerlendirilen yanıtlar (sayfalı) |
| GET | `/api/v1/admin/logs` | Sistem logları (sayfalı) |
| GET | `/api/v1/admin/load-history` | Son 24 saatlik sistem yükü (saatlik bucket) |

> Sayfalı endpoint'ler `?limit=20&offset=0` query parametrelerini ve `{items, total, limit, offset}` response formatını kullanır.

---

## Mimari Notlar

### Agentic RAG Akışı

```
Mesaj geldi
  → university_id yoksa → GPT ile üniversite tespiti
    → DB'de yoksa → GPT ile bilgi üret + DB'ye kaydet
  → Crawl edilmemişse → Playwright ile crawl (arka planda)
    → 0 belge → çok kademeli URL keşfi → tekrar crawl
  → ask() → cosine similarity ≥ 0.60 → GPT ile yanıt üret
  → skor < 0.60 → hedefli PDF arama → soruya özel crawl → retry
  → threshold 0.35'e düşür → son deneme
  → hâlâ boş → fallback mesajı + resmi mevzuat sayfası linki
```

### Şifre Sıfırlama

Stateless JWT reset token (30 dk TTL, `type=pwd_reset` claim). E-posta gönderimi `fastapi-mail` ile SMTP üzerinden yapılır. SMTP ayarları boş bırakılırsa token backend log'una yazılır — geliştirme ortamı için yeterli.

### Obsolete Belge Temizliği

`POST /universities/{id}/crawl` ile tetiklenen admin re-crawl'da crawler, kaynak sitedeki mevcut URL'leri döner. DB'de olup yeni crawl'da bulunmayan belgeler Qdrant + PostgreSQL'den silinir. Güvenlik eşiği: mevcut belgelerin %80'inden fazlası silinecekse işlem iptal edilir.

### Frontend Docker

Multi-stage Dockerfile: `node:20-alpine` ile `npm run build` → `nginx:1.27-alpine` ile statik serve. SPA fallback (`try_files $uri /index.html`), gzip compression ve statik asset cache header'ları yapılandırılmıştır.

### Periyodik Crawl

Uygulama başlarken APScheduler devreye girer. `CRAWL_INTERVAL_HOURS` (varsayılan 24) saatte bir `is_crawled=True` olan tüm üniversiteler yeniden crawl + embed edilir. Scheduler crawl'ları `cleanup_obsolete=False` ile çalıştırır — otomatik silme yalnızca admin manuel re-crawl'da aktiftir.

### Logging

Her modül `get_logger("modül_adı")` ile JSON logger alır. Her kritik işlem `start_operation()` → `add_field()` → `succeed()` / `fail()` döngüsüyle izlenir:

```json
{"timestamp":"2026-06-01T10:23:01.123Z","level":"INFO","logger":"unilex.chat_service",
 "operation_name":"answer_question","session_id":5,"university_id":1,
 "chunks_retrieved":8,"max_score":0.81,"answer_len":420,"status":"succeeded","duration_ms":1340}
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
| UNILEX_009 | `MessageNotFoundError` | 404 |
