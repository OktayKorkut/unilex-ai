# Unilex AI

Üniversite mevzuatlarını otomatik olarak toplayıp kullanıcıların sorularını yapay zeka ile yanıtlayan bir RAG (Retrieval-Augmented Generation) sistemi.

## Ne Yapıyor?

1. Kullanıcı sisteme kayıt olur ve üniversitesini seçer
2. Agent, seçilen üniversitenin web sitesinden mevzuat belgelerini otomatik çeker
3. Belgeler parçalanır, vektörleştirilir ve veritabanına kaydedilir
4. Kullanıcı sorularını yazar, sistem ilgili belgeleri bularak yapay zeka ile yanıt üretir

## Tech Stack

| Katman | Teknoloji |
|---|---|
| Backend | FastAPI (Python) |
| Crawler | Playwright |
| LLM | OpenAI gpt-4o-mini |
| Embeddings | OpenAI text-embedding-3-small |
| Vector DB | Qdrant |
| Database | PostgreSQL |
| Auth | JWT |

## Proje Yapısı

```
unilex-ai/
├── backend/
│   ├── app/
│   │   ├── api/routers/       # HTTP endpoint'leri (auth, universities, chat)
│   │   ├── core/              # Config ve güvenlik (JWT, şifreleme)
│   │   ├── db/                # Veritabanı modelleri ve bağlantı
│   │   ├── crawler/           # Playwright ile mevzuat çekme (Faz 2)
│   │   ├── rag/               # Embedding ve retrieval işlemleri (Faz 3)
│   │   ├── agent/             # Soru-cevap agent'ı (Faz 4)
│   │   └── main.py            # Uygulama giriş noktası
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── docker-compose.yml
└── README.md
```

## Geliştirme Fazları

| Faz | Konu | Durum |
|---|---|---|
| Faz 1 | Proje iskeleti, auth, Docker | ✅ Tamamlandı |
| Faz 2 | Playwright crawler | 🔜 Sıradaki |
| Faz 3 | RAG pipeline (embed + retrieve) | ⏳ Bekliyor |
| Faz 4 | Agent + chat endpoint | ⏳ Bekliyor |
| Faz 5 | Polish, testler, dokümantasyon | ⏳ Bekliyor |

---

## Kurulum (İlk Kez Çalıştıranlar İçin)

### Gereksinimler

Bilgisayarında şunlar kurulu olmalı:

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Python 3.11+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/)

### 1. Repoyu Klonla

```bash
git clone https://github.com/OktayKorkut/unilex-ai.git
cd unilex-ai
```

### 2. Environment Dosyasını Oluştur

```bash
cp backend/.env.example backend/.env
```

Ardından `backend/.env` dosyasını aç ve şu alanları doldur:

```
OPENAI_API_KEY=sk-...         # OpenAI API anahtarın
SECRET_KEY=...                # Rastgele güçlü bir string (aşağıdaki komutla üretebilirsin)
DATABASE_URL=postgresql://unilex:unilex123@postgres:5432/unilex 
```

`SECRET_KEY` üretmek için terminalde:
```bash
openssl rand -hex 32
```

### 3. Docker ile Başlat

```bash
docker compose up --build
```

İlk çalıştırmada biraz uzun sürebilir (image'lar indirilir, Playwright kurulur).

Çalıştıktan sonra:

| Servis | Adres |
|---|---|
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| Qdrant Dashboard | http://localhost:6333/dashboard |

### 4. Sağlık Kontrolü

```bash
curl http://localhost:8000/health
```

`{"status":"ok","app":"Unilex AI"}` görüyorsan her şey çalışıyor.

---

## API Endpoints

### Auth

| Method | Endpoint | Açıklama |
|---|---|---|
| POST | `/api/v1/auth/register` | Yeni kullanıcı kaydı |
| POST | `/api/v1/auth/login` | Giriş yap, token al |

**Kayıt örneği:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"123456","full_name":"Test User"}'
```

**Giriş örneği:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"123456"}'
```

### Üniversiteler

| Method | Endpoint | Açıklama |
|---|---|---|
| GET | `/api/v1/universities/` | Tüm üniversiteleri listele |

---

## Katkıda Bulunma

Başlamadan önce `docker compose up` ile ortamın ayakta olduğundan emin ol, değişikliklerini kendi branch'ine push'la.

```bash
git checkout -b feature/yaptığın-şey
# ... değişikliklerini yap ...
git add .
git commit -m "feat: açıklama"
git push origin feature/yaptığın-şey
```
