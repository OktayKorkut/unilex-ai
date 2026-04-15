import io
import httpx
from datetime import datetime
from playwright.async_api import async_playwright, Page
from pypdf import PdfReader
from sqlalchemy.orm import Session
from app.db.models import University, Document
from app.rag.embedder import embed_university_documents


MEVZUAT_KEYWORDS = [
    "yönetmelik", "yönerge", "statü", "esaslar", "tüzük",
    "mevzuat", "kural", "ilke", "karar", "kanun", "uygulama",
    "yönetim", "akademik", "disiplin", "sınav", "öğrenci",
]


class UniversityCrawler:

    def _is_relevant_pdf(self, title: str, url: str) -> bool:
        text = (title + " " + url).lower()
        return any(kw in text for kw in MEVZUAT_KEYWORDS)

    async def crawl(self, university: University, db: Session) -> dict:
        result = {"documents_added": 0, "pdfs_found": 0, "errors": []}

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            )
            page = await context.new_page()

            try:
                await page.goto(university.mevzuat_url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(2000)

                pdf_links = await self._extract_pdf_links(page)
                pdf_links = [
                    (url, title) for url, title in pdf_links
                    if self._is_relevant_pdf(title, url)
                ]
                result["pdfs_found"] = len(pdf_links)

                if not pdf_links:
                    page_text = await self._extract_page_text(page)
                    if len(page_text.strip()) > 200:
                        self._save_document(
                            db=db,
                            university_id=university.id,
                            title=f"{university.name} - Mevzuat",
                            content=page_text,
                            source_url=university.mevzuat_url,
                        )
                        result["documents_added"] += 1

                async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, verify=False) as client:
                    for pdf_url, pdf_title in pdf_links:
                        try:
                            text = await self._extract_pdf_text(client, pdf_url)
                            if text and len(text.strip()) > 100:
                                self._save_document(
                                    db=db,
                                    university_id=university.id,
                                    title=pdf_title or f"{university.name} - Belge",
                                    content=text,
                                    source_url=pdf_url,
                                )
                                result["documents_added"] += 1
                        except Exception as e:
                            result["errors"].append(f"{pdf_url}: {str(e)}")

                university.is_crawled = True
                university.crawled_at = datetime.utcnow()
                db.commit()

                chunks_added = embed_university_documents(university.id, db)
                result["chunks_embedded"] = chunks_added

            except Exception as e:
                result["errors"].append(f"Sayfa yüklenemedi: {str(e)}")
            finally:
                await browser.close()

        return result

    async def _extract_pdf_links(self, page: Page) -> list[tuple[str, str]]:
        links = await page.evaluate("""
            () => {
                return Array.from(document.querySelectorAll('a[href]'))
                    .filter(a => a.href.toLowerCase().includes('.pdf'))
                    .map(a => [a.href, a.textContent.trim().replace(/\\s+/g, ' ')])
                    .filter(([href]) => href.startsWith('http'));
            }
        """)
        seen = set()
        unique = []
        for url, title in links:
            if url not in seen:
                seen.add(url)
                unique.append((url, title))
        return unique

    async def _extract_page_text(self, page: Page) -> str:
        return await page.evaluate("""
            () => {
                const selectors = ['main', 'article', '.content', '#content', '#main', '.page-content', 'body'];
                for (const sel of selectors) {
                    const el = document.querySelector(sel);
                    if (el && el.innerText.trim().length > 200) return el.innerText;
                }
                return document.body.innerText;
            }
        """)

    async def _extract_pdf_text(self, client: httpx.AsyncClient, url: str) -> str:
        response = await client.get(url)
        response.raise_for_status()
        reader = PdfReader(io.BytesIO(response.content))
        pages_text = []
        for pdf_page in reader.pages:
            text = pdf_page.extract_text()
            if text:
                pages_text.append(text.strip())
        return "\n\n".join(pages_text)

    def _save_document(self, db, university_id, title, content, source_url):
        exists = db.query(Document).filter(Document.source_url == source_url).first()
        if not exists:
            db.add(Document(
                university_id=university_id,
                title=title[:255],
                content=content,
                source_url=source_url,
            ))
            db.commit()
