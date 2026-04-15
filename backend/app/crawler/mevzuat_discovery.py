"""
Bir üniversitenin mevzuat sayfasını dört kademeli stratejyle bulur:
  1. Yaygın URL pattern'larını dene (hızlı)
  2. sitemap.xml tara (güvenilir)
  3. Ana sayfadaki linkleri tara — Playwright 1. seviye
  4. Ara sayfaları takip et — Playwright 2. seviye (kurumsal, üniversitemiz vb.)
"""

import httpx
from xml.etree import ElementTree
from playwright.async_api import async_playwright

from app.core.logger import get_logger

logger = get_logger("mevzuat_discovery")

COMMON_PATTERNS = [
    "/mevzuat", "/mevzuat/", "/tr/mevzuat", "/tr/mevzuat/",
    "/tr/mevzuat/mevzuat.php", "/universite/mevzuat", "/universitemiz/mevzuat",
    "/kurumsal/mevzuat", "/hakkinda/mevzuat", "/hakkimizda/mevzuat",
    "/icerik/mevzuat", "/tr/icerik/mevzuat", "/universitehakkinda/mevzuat",
    "/kurumsalkimlik/mevzuat", "/tr/universitemiz/mevzuat", "/tr/kurumsal/mevzuat",
    "/tr/hakkinda/mevzuat",
    "/yonetmelik", "/yonetmelikler", "/tr/yonetmelikler", "/yonetmelik-ve-yonerge",
    "/universitemiz/yonetmelik-ve-yonerge", "/kurumsal/yonetmelikler",
    "/tr/kurumsal/yonetmelikler", "/tr/yonetmelik", "/icerik/yonetmelikler",
    "/tr/icerik/yonetmelikler", "/hakkinda/yonetmelikler", "/universite/yonetmelikler",
    "/yonerge", "/yonergeler", "/tr/yonergeler", "/kurumsal/yonergeler",
    "/tr/kurumsal/yonergeler",
    "/statu", "/tuzuk", "/tr/statu", "/tr/tuzuk",
]

MEVZUAT_SIGNALS = [
    "yönetmelik", "yönerge", "mevzuat", "tüzük", "statü",
    "yonetmelik", "yonerge", "regulation",
]

SITEMAP_SIGNALS = ["mevzuat", "yonetmelik", "yönetmelik", "yönerge", "regulations"]

INTERMEDIATE_SIGNALS = [
    "kurumsal", "üniversitemiz", "universitemiz", "hakkımızda", "hakkimizda",
    "hakkında", "hakkinda", "about", "university", "kurum",
]


def _extract_base(url: str) -> str:
    parts = url.split("/")
    return "/".join(parts[:3])


def _is_mevzuat_page(html: str) -> bool:
    h = html.lower()
    if ".pdf" in h:
        for signal in MEVZUAT_SIGNALS:
            idx = h.find(".pdf")
            while idx != -1:
                surrounding = h[max(0, idx - 150):idx + 10]
                if signal in surrounding:
                    return True
                idx = h.find(".pdf", idx + 1)
    hits = sum(1 for s in MEVZUAT_SIGNALS if s in h)
    return hits >= 3


def _score_link(href: str, text: str) -> int:
    combined = (href + " " + text).lower()
    return sum(1 for s in MEVZUAT_SIGNALS if s in combined)


async def _try_patterns(base: str, skip_url: str) -> "str | None":
    skip = skip_url.rstrip("/")
    async with httpx.AsyncClient(timeout=8.0, follow_redirects=True, verify=False) as client:
        for pattern in COMMON_PATTERNS:
            url = base + pattern
            if url.rstrip("/") == skip:
                continue
            try:
                r = await client.get(url)
                final = str(r.url).rstrip("/")
                if r.status_code == 200 and final != base.rstrip("/") and final != skip:
                    if _is_mevzuat_page(r.text):
                        logger.info({"event": "pattern_match", "url": final})
                        return final
            except Exception:
                continue
    return None


async def _try_sitemap(base: str) -> "str | None":
    async with httpx.AsyncClient(timeout=8.0, follow_redirects=True, verify=False) as client:
        for path in ["/sitemap.xml", "/sitemap_index.xml", "/tr/sitemap.xml"]:
            try:
                r = await client.get(base + path)
                if r.status_code != 200:
                    continue
                root = ElementTree.fromstring(r.text)
                ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
                for loc in root.findall(".//s:loc", ns):
                    link = loc.text or ""
                    if any(s in link.lower() for s in SITEMAP_SIGNALS):
                        logger.info({"event": "sitemap_match", "url": link})
                        return link
            except Exception:
                continue
    return None


async def _get_all_links(page) -> list[dict]:
    return await page.evaluate("""
        () => Array.from(document.querySelectorAll('a[href]'))
            .map(a => ({ href: a.href, text: (a.textContent || '').trim().toLowerCase() }))
            .filter(l => l.href.startsWith('http') && !l.href.includes('#'))
    """)


async def _try_deep_crawl(base: str, skip_url: str) -> "str | None":
    skip = skip_url.rstrip("/")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(base, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(1500)
            links = await _get_all_links(page)

            mevzuat_links = [
                (l["href"], _score_link(l["href"], l["text"]))
                for l in links
                if _score_link(l["href"], l["text"]) > 0 and l["href"].rstrip("/") != skip
            ]
            if mevzuat_links:
                mevzuat_links.sort(key=lambda x: -x[1])
                found = mevzuat_links[0][0]
                logger.info({"event": "deep_crawl_level1_match", "url": found})
                return found

            intermediate = []
            seen: set[str] = set()
            for l in links:
                href = l["href"]
                if (base in href and href not in seen
                        and any(s in l["text"] or s in href.lower() for s in INTERMEDIATE_SIGNALS)):
                    seen.add(href)
                    intermediate.append(href)

            for inter_url in intermediate[:5]:
                try:
                    await page.goto(inter_url, wait_until="domcontentloaded", timeout=15000)
                    await page.wait_for_timeout(1000)
                    sub_links = await _get_all_links(page)
                    mevzuat_sub = [
                        (l["href"], _score_link(l["href"], l["text"]))
                        for l in sub_links
                        if _score_link(l["href"], l["text"]) > 0 and l["href"].rstrip("/") != skip
                    ]
                    if mevzuat_sub:
                        mevzuat_sub.sort(key=lambda x: -x[1])
                        found = mevzuat_sub[0][0]
                        logger.info({"event": "deep_crawl_level2_match", "url": found, "via": inter_url})
                        return found
                except Exception:
                    continue

        except Exception:
            logger.error({"event": "deep_crawl_error", "base": base})
        finally:
            await browser.close()
    return None


async def discover_mevzuat_url(current_url: str) -> "str | None":
    """
    Verilen URL'den başlayarak üniversitenin gerçek mevzuat sayfasını bulur.
    Başarısız olursa None döner.
    """
    op = logger.start_operation("discover_mevzuat_url")
    op.add_field("current_url", current_url)

    base = _extract_base(current_url)

    url = await _try_patterns(base, skip_url=current_url)
    if url:
        op.add_field("strategy", "pattern").add_field("found_url", url).succeed()
        return url

    url = await _try_sitemap(base)
    if url:
        op.add_field("strategy", "sitemap").add_field("found_url", url).succeed()
        return url

    url = await _try_deep_crawl(base, skip_url=current_url)
    if url:
        op.add_field("strategy", "deep_crawl").add_field("found_url", url).succeed()
    else:
        op.add_field("result", "not_found").fail(exc_info=False)
    return url
