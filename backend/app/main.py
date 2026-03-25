from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from qdrant_client import QdrantClient
from app.core.config import settings
from app.db.database import Base, engine, get_db
from app.api.routers import auth, universities, chat, users

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.APP_NAME, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(universities.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")


@app.get("/health")
def health(db: Session = Depends(get_db)):
    postgres_status = "disconnected"
    qdrant_status = "disconnected"

    # PostgreSQL Test
    try:
        db.execute(text("SELECT 1"))
        postgres_status = "connected"
    except Exception:
        pass

    # Qdrant Test
    try:
        qdrant = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        qdrant.get_collections()
        qdrant_status = "connected"
    except Exception:
        pass

    overall_status = "ok" if postgres_status == "connected" and qdrant_status == "connected" else "error"

    return {
        "status": overall_status,
        "postgres": postgres_status,
        "qdrant": qdrant_status,
        "app": settings.APP_NAME
    }
