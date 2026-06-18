from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import settings
from app.core.logger import get_logger
from app.db.database import SessionLocal
from app.db.models import University
from app.services.crawl_job_service import run_crawl_job

logger = get_logger("scheduler")

_scheduler = AsyncIOScheduler()


async def _crawl_all_universities() -> None:
    db = SessionLocal()
    try:
        universities = (
            db.query(University)
            .filter(University.is_crawled == True, University.crawl_status != "running") 
            .all()
        )
        ids = [u.id for u in universities]
    finally:
        db.close()

    for uni_id in ids:
        logger.info({"event": "scheduled_crawl_triggered", "university_id": uni_id})
        await run_crawl_job(uni_id)


def start_scheduler() -> None:
    _scheduler.add_job(
        _crawl_all_universities,
        trigger="interval",
        hours=settings.CRAWL_INTERVAL_HOURS,
        id="crawl_all_universities",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info({"event": "scheduler_started", "interval_hours": settings.CRAWL_INTERVAL_HOURS})


def stop_scheduler() -> None:
    _scheduler.shutdown(wait=False)
    logger.info({"event": "scheduler_stopped"})
