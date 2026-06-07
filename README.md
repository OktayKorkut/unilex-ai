# UniLex AI

Üniversite akademik mevzuatını doğal dilde sorgulanabilir hale getiren yapay zeka destekli sohbet asistanı.

---

## Problem

Üniversite yönetmelikleri ve yönergeleri uzun, karmaşık PDF belgelerinde dağınık biçimde yayımlanır. Bir öğrencinin "Çift anadal başvurusu için GNO şartı nedir?" gibi basit bir soruyu yanıtlayabilmek için bazen birden fazla belgeyi okuyup karşılaştırması gerekir.

UniLex AI bu süreci otomatikleştirir: resmi belgeler sisteme otomatik olarak toplanır ve öğrenci sorularını doğrudan bu belgelerden yanıtlar.

---

## Nasıl Çalışır?

1. **Otomatik veri toplama** — Playwright tabanlı web crawler, üniversitenin mevzuat sayfasındaki PDF belgelerini periyodik olarak indirir ve metne dönüştürür.
2. **Semantik indeksleme** — Belgeler 800 kelimelik parçalara bölünür, OpenAI `text-embedding-3-small` ile vektöre dönüştürülerek Qdrant'a yüklenir.
3. **RAG pipeline** — Kullanıcı sorusu gelince vektör tabanında anlamsal arama yapılır; en ilgili parçalar `gpt-4o-mini` modeline bağlam olarak iletilir.
4. **Agentic fallback** — Skor eşiğinin altında kalırsa sistem soruya özel bir hedefli crawl başlatır, eksik belgeyi indirir ve yanıtı yeniden dener.
5. **Kaynak şeffaflığı** — Her yanıt, kullanılan belgenin adı ve bağlantısıyla birlikte sunulur.

---

## Özellikler

- **Sohbet arayüzü** — Geçmiş oturumlar, yanıt yenileme, kaynak belge görüntüleme
- **Admin paneli** — Crawler yönetimi, sistem logları, kullanıcı ve geri bildirim takibi
- **Kimlik doğrulama** — JWT tabanlı oturum, Bcrypt şifreleme, e-posta ile şifre sıfırlama
- **KVKK uyumu** — Kullanıcı verisi anonimleştirme ve hesap silme
- **Periyodik güncelleme** — APScheduler ile her 24 saatte bir otomatik yeniden tarama

---

## Teknoloji

| Katman | Teknoloji |
|--------|-----------|
| Backend | FastAPI + Python 3.11 |
| Frontend | React 19 + Vite + Mantine UI v9 + GSAP |
| LLM | OpenAI gpt-4o-mini |
| Embedding | OpenAI text-embedding-3-small (1536 boyut) |
| Vektör Veritabanı | Qdrant |
| İlişkisel Veritabanı | PostgreSQL 16 + SQLAlchemy 2.0 + Alembic |
| Web Crawler | Playwright |
| Altyapı | Docker Compose + Nginx |

---

## Kurulum

### Gereksinimler

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### 1. Repoyu Klonla

```bash
git clone https://github.com/OktayKorkut/unilex-ai.git
cd unilex-ai
```

### 2. Ortam Değişkenlerini Ayarla

```bash
cp backend/.env.example backend/.env
```

`backend/.env` dosyasını düzenle:

```env
OPENAI_API_KEY=sk-...
SECRET_KEY=...        # openssl rand -hex 32
```

Diğer değerler (veritabanı bağlantıları vb.) varsayılan Docker Compose yapılandırmasıyla çalışır.

> **SMTP (isteğe bağlı):** Şifre sıfırlama e-postası için `.env` dosyasına `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD` ve `SMTP_FROM` değerlerini ekle. Boş bırakılırsa sıfırlama token'ı backend loguna yazılır.

### 3. Başlat

```bash
docker compose up --build
```

| Servis | Adres |
|--------|-------|
| Uygulama | http://localhost:3000 |
| API (Swagger) | http://localhost:8000/docs |

---

## Geliştirme Süreci

| Faz | Konu |
|-----|------|
| 1 | Proje iskeleti, kimlik doğrulama, Docker |
| 2 | Playwright crawler, PDF indirme ve metin çıkarma |
| 3 | RAG pipeline — chunking, embedding, vektör arama |
| 4 | Agentic chat — üniversite tespiti, URL keşfi, hedefli crawl |
| 5 | Kod kalitesi — loglama, exception handling, servis katmanı |
| 6 | Alembic migration sistemi, admin paneli, KVKK, periyodik crawl |
| 7 | React frontend — chat, profil, admin dashboard |
| 8 | Şifre sıfırlama, obsolete belge temizliği, sayfalama, Nginx container |

---

## Lisans

Bu proje Işık Üniversitesi COMP/SOFT 4902 Mezuniyet Tasarım Projesi kapsamında geliştirilmiştir.

**Oktay Korkut** (21COMP1046) · **Betül Taşkıran** (21SOFT1047)  
