from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from qdrant_client import QdrantClient

from app.core.config import settings
from app.core.exceptions import add_exception_handler
from app.core.logger import get_logger
from app.core.scheduler import start_scheduler, stop_scheduler
from app.db.database import get_db, engine, Base
from app.db import models
from app.api.routers import auth, universities, chat, users, documents, crawler, admin, feedback

# Safe creation of any new tables (like feedbacks)
Base.metadata.create_all(bind=engine)

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title=settings.APP_NAME, version="0.1.0", lifespan=lifespan)


add_exception_handler(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(universities.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(crawler.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(feedback.router, prefix="/api/v1")

logger.info({"event": "startup", "app": settings.APP_NAME})


@app.get("/health")
def health(db: Session = Depends(get_db)):
    postgres_status = "disconnected"
    qdrant_status = "disconnected"

    try:
        db.execute(text("SELECT 1"))
        postgres_status = "connected"
    except Exception:
        logger.error({"event": "health_check_postgres_failed"})

    try:
        qdrant = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        qdrant.get_collections()
        qdrant_status = "connected"
    except Exception:
        logger.error({"event": "health_check_qdrant_failed"})

    overall = "ok" if postgres_status == "connected" and qdrant_status == "connected" else "error"
    return {
        "status": overall,
        "postgres": postgres_status,
        "qdrant": qdrant_status,
        "app": settings.APP_NAME,
    }
