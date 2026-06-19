"""
Kullanıcı sorusuna göre mevzuat sayfasından ilgili PDF'leri bulup indirir.
"""

import json

import fitz
import httpx
from playwright.async_api import async_playwright
from openai import OpenAI
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logger import get_logger
from app.core.text_utils import fix_turkish_encoding
from app.db.models import Document, University

logger = get_logger("targeted_crawler")


async def _get_pdf_links(url: str) -> list[tuple[str, str]]:
    """Mevzuat sayfasındaki tüm PDF linklerini ve başlıklarını döner. Sekmeleri tıklayarak gizli içerikleri de tarar."""
    op = logger.start_operation("get_pdf_links")
    op.add_field("url", url)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)

            seen: set[str] = set()
            result: list[tuple[str, str]] = []

            async def collect():
                links = await page.evaluate("""
                    () => Array.from(document.querySelectorAll('a[href]'))
                        .filter(a => a.href.toLowerCase().includes('.pdf'))
                        .map(a => [a.href, a.textContent.trim().replace(/\\s+/g, ' ')])
                        .filter(([href]) => href.startsWith('http'))
                """)
                for href, title in links:
                    if href not in seen:
                        seen.add(href)
                        result.append((href, title))

            await collect()

            # Sekme navigation varsa her sekmeye tıkla
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
                    if page.url == url:
                        await collect()
                    else:
                        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                        await page.wait_for_timeout(1000)
                except Exception:
                    continue

            op.add_field("pdf_count", len(result)).succeed()
            return result
        except Exception:
            op.fail()
            return []
        finally:
            await browser.close()


def _rank_pdfs_by_question(
    question: str, pdf_links: list[tuple[str, str]]
) -> list[tuple[str, str]]:
    """GPT'ye soruyu ve PDF listesini vererek en ilgili 3 PDF'i seçtirir."""
    if not pdf_links:
        return []

    op = logger.start_operation("rank_pdfs_by_question")
    op.add_field("pdf_count", len(pdf_links))

    pdf_list = [{"index": i, "title": title, "url": url} for i, (url, title) in enumerate(pdf_links)]

    try:
        openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = openai_client.chat.completions.create(
            model=settings.LLM_MODEL,
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Kullanıcının sorusuna en uygun PDF belgelerini seç. "
                        "Sadece JSON döndür: {\"selected\": [<index>, <index>, ...]} "
                        "En fazla 3 belge seç. Hiç uygun yoksa boş liste döndür."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Soru: {question}\n\nPDF listesi:\n{json.dumps(pdf_list, ensure_ascii=False)}",
                },
            ],
            response_format={"type": "json_object"},
        )
        result = json.loads(response.choices[0].message.content)
        selected_indices = result.get("selected", [])
        selected = [pdf_links[i] for i in selected_indices if i < len(pdf_links)]
        op.add_field("selected_count", len(selected)).succeed()
        return selected
    except Exception:
        op.fail()
        return []


async def _download_pdf_text(url: str) -> str:
    """PDF'i indir ve metni çıkar."""
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, verify=False) as client:
        response = await client.get(url)
        response.raise_for_status()
        doc = fitz.open(stream=response.content, filetype="pdf")
        pages_text = [p.get_text().strip() for p in doc if p.get_text()]
        doc.close()
        return fix_turkish_encoding("\n\n".join(pages_text))


async def search_and_embed_for_question(
    question: str,
    university: University,
    db: Session,
) -> int:
    """
    Soruya özel PDF arar, indirir, DB'ye kaydeder ve embed eder.

    Returns:
        Eklenen yeni belge sayısı.
    """
    from app.rag.embedder import embed_document

    op = logger.start_operation("search_and_embed_for_question")
    op.add_field("university_id", university.id)

    pdf_links = await _get_pdf_links(university.mevzuat_url)
    if not pdf_links:
        op.add_field("result", "no_pdf_links").fail(exc_info=False)
        return 0

    relevant = _rank_pdfs_by_question(question, pdf_links)
    if not relevant:
        op.add_field("result", "no_relevant_pdfs").fail(exc_info=False)
        return 0

    added = 0
    for pdf_url, pdf_title in relevant:
        exists = db.query(Document).filter(Document.source_url == pdf_url).first()
        if exists:
            continue
        try:
            text = await _download_pdf_text(pdf_url)
            if not text or len(text.strip()) < 100:
                continue
            doc = Document(
                university_id=university.id,
                title=(pdf_title or f"{university.name} - Belge")[:255],
                content=text,
                source_url=pdf_url,
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)
            embed_document(doc)
            added += 1
            logger.info({"event": "pdf_embedded", "url": pdf_url, "university_id": university.id})
        except Exception:
            logger.error({"event": "pdf_embed_failed", "url": pdf_url})
            continue

    op.add_field("added", added).succeed()
    return added
