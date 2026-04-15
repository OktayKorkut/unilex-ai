import json
import re

from openai import OpenAI
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logger import get_logger
from app.db.models import University

logger = get_logger("university_finder")


def find_or_create_university(university_name: str, db: Session) -> "University | None":
    """
    Verilen üniversite adı için GPT'ye domain ve mevzuat URL'i tahmin ettirir,
    DB'ye ekler ve University nesnesini döner.
    DB'de zaten varsa mevcut kaydı döner.
    """
    op = logger.start_operation("find_or_create_university")
    op.add_field("university_name", university_name)

    try:
        openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = openai_client.chat.completions.create(
            model=settings.LLM_MODEL,
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Türk üniversitelerinin resmi web sitelerini çok iyi biliyorsun. "
                        "Verilen üniversite için JSON döndür:\n"
                        "{\n"
                        '  "name": "<üniversitenin tam resmi adı>",\n'
                        '  "slug": "<kısa slug, sadece küçük harf, rakam ve tire>",\n'
                        '  "domain": "<ana domain, örn: biruni.edu.tr>",\n'
                        '  "mevzuat_url": "<mevzuat/yönetmelik sayfasının tahmini URL\'i>"\n'
                        "}\n"
                        "Tüm alanlar dolu olmalı. Emin değilsen en mantıklı tahmini yap."
                    ),
                },
                {"role": "user", "content": f"Üniversite: {university_name}"},
            ],
            response_format={"type": "json_object"},
        )

        data = json.loads(response.choices[0].message.content)
        name = data.get("name")
        slug = data.get("slug")
        mevzuat_url = data.get("mevzuat_url")
        domain = data.get("domain", "")
        op.add_field("gpt_name", name).add_field("gpt_mevzuat_url", mevzuat_url)

        if not name or not slug or not mevzuat_url:
            op.add_field("result", "incomplete_gpt_response").fail(exc_info=False)
            return None
        if not mevzuat_url.startswith("http"):
            op.add_field("result", "invalid_url").fail(exc_info=False)
            return None

        slug = re.sub(r"[^a-z0-9-]", "", slug.lower())[:100]

        existing = db.query(University).filter(
            (University.slug == slug) | (University.name == name)
        ).first()
        if existing:
            op.add_field("result", "existing_record").succeed()
            return existing

        new_uni = University(name=name, slug=slug, mevzuat_url=mevzuat_url)
        new_uni._discovery_domain = domain
        db.add(new_uni)
        db.commit()
        db.refresh(new_uni)
        new_uni._discovery_domain = domain

        op.add_field("result", "created").add_field("university_id", new_uni.id).succeed()
        return new_uni

    except Exception:
        op.fail()
        return None
