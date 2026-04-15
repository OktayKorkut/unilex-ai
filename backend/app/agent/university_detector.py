import json

from openai import OpenAI
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logger import get_logger
from app.db.models import University

logger = get_logger("university_detector")


def detect_university(message: str, db: Session) -> tuple["University | None", "str | None"]:
    """
    Kullanıcı mesajından üniversite ismini çıkarır ve DB'de eşleştirir.

    Returns:
        (matched_university, detected_name)
        Her ikisi de None olabilir (üniversite tespit edilemedi).
    """
    op = logger.start_operation("detect_university")

    universities = db.query(University).all()
    uni_list = [{"id": u.id, "name": u.name, "slug": u.slug} for u in universities]

    try:
        openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = openai_client.chat.completions.create(
            model=settings.LLM_MODEL,
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Kullanıcı mesajından bir Türk üniversitesi adı tespit et. "
                        "Verilen listeden en uygun eşleşmeyi bul. "
                        "Sadece JSON döndür: "
                        "{\"id\": <int veya null>, \"detected_name\": <string veya null>} "
                        "id: listede bulunan üniversitenin id'si, bulunamazsa null. "
                        "detected_name: mesajdan tespit edilen üniversite adı (listede olmasa bile), yoksa null."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Üniversite listesi:\n{json.dumps(uni_list, ensure_ascii=False)}\n\nMesaj: {message}",
                },
            ],
            response_format={"type": "json_object"},
        )

        result = json.loads(response.choices[0].message.content)
        uni_id = result.get("id")
        detected_name = result.get("detected_name")
        op.add_field("detected_name", detected_name).add_field("matched_id", uni_id)

        matched = None
        if uni_id is not None:
            matched = db.query(University).filter(University.id == uni_id).first()

        op.succeed()
        return matched, detected_name

    except Exception:
        op.fail()
        return None, None
