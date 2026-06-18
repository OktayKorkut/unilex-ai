import io
import httpx
from datetime import datetime, timezone
from playwright.async_api import async_playwright, Page
from pypdf import PdfReader
from sqlalchemy.orm import Session
from app.db.models import University, Document
from app.core.logger import get_logger
from app.services.system_log_service import create_system_log

logger = get_logger("crawler")


class UniversityCrawler:

    async def crawl(self, university: University, db: Session) -> dict:
        result = {"documents_added": 0, "pdfs_found": 0, "errors": [], "discovered_source_urls": []}

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                ignore_https_errors=True,
            )
            page = await context.new_page()

            try:
                await page.goto(university.mevzuat_url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(2000)

                pdf_links = await self._extract_pdf_links(page)
                result["pdfs_found"] = len(pdf_links)
                discovered: set[str] = set()

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
                        discovered.add(university.mevzuat_url)
                else:
                    # Track all found PDF links as discovered (even if download fails)
                    for pdf_url, _ in pdf_links:
                        discovered.add(pdf_url)

                async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, verify=False) as client:
                    for pdf_url, pdf_title in pdf_links:
                        try:
                            text = await self._extract_pdf_text(client, pdf_url)
                            if not text:
                                reason = "PDF'den metin çıkarılamadı (bozuk encoding veya görsel PDF)"
                                result["errors"].append(f"{pdf_url}: {reason}")
                                create_system_log(db, "warning", "PDF Atlandı", f"[{university.name}] {pdf_title or 'Başlıksız'}: {reason}\n{pdf_url}")
                            elif len(text.strip()) <= 100:
                                reason = f"Metin çok kısa ({len(text.strip())} karakter)"
                                result["errors"].append(f"{pdf_url}: {reason}")
                                create_system_log(db, "warning", "PDF Atlandı", f"[{university.name}] {pdf_title or 'Başlıksız'}: {reason}\n{pdf_url}")
                            else:
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
                            create_system_log(db, "error", "PDF İndirme Hatası", f"[{university.name}] {pdf_title or 'Başlıksız'}: {str(e)[:250]}\n{pdf_url}")

                result["discovered_source_urls"] = list(discovered)

                university.is_crawled = True
                university.crawled_at = datetime.now(timezone.utc)
                db.commit()

            except Exception as e:
                result["errors"].append(f"Sayfa yüklenemedi: {str(e)}")
            finally:
                await browser.close()

        return result

    async def _extract_pdf_links(self, page: Page) -> list[tuple[str, str]]:
        seen: set[str] = set()
        result: list[tuple[str, str]] = []
        base_url = page.url

        async def collect():
            links = await page.evaluate("""
                () => Array.from(document.querySelectorAll('a[href]'))
                    .filter(a => a.href.toLowerCase().includes('.pdf'))
                    .map(a => [a.href, a.textContent.trim().replace(/\\s+/g, ' ')])
                    .filter(([href]) => href.startsWith('http'))
            """)
            for url, title in links:
                if url not in seen:
                    seen.add(url)
                    result.append((url, title))

        await collect()

        # Sekme (tab) navigation varsa her sekmeye tıkla ve linkleri topla
        tab_selectors = (
            '[role="tab"], [data-toggle="tab"], [data-bs-toggle="tab"], '
            '.nav-tabs a, .nav-tabs button, .tab-nav a, .tab-nav button, '
            '.tabs-nav button, .tabs-nav a'
        )
        tabs = await page.query_selector_all(tab_selectors)

        for tab in tabs:
            try:
                await tab.click()
                await page.wait_for_timeout(800)
                if page.url != base_url:
                    await page.goto(base_url, wait_until="domcontentloaded", timeout=15000)
                    await page.wait_for_timeout(1000)
                else:
                    await collect()
            except Exception:
                continue

        return result

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
        raw = "\n\n".join(pages_text).replace("\x00", "")
        # PDFs with unresolved Unicode escape sequences (/uniXXXX) are garbled — unusable for RAG
        if raw and raw.count("/uni") > len(raw) / 20:
            return ""
        return raw

    def _save_document(self, db, university_id, title, content, source_url):
        try:
            exists = db.query(Document).filter(Document.source_url == source_url).first()
            if not exists:
                db.add(Document(
                    university_id=university_id,
                    title=title[:255],
                    content=content,
                    source_url=source_url,
                ))
                db.commit()
        except Exception:
            db.rollback()
            raise
