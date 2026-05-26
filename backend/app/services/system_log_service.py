from sqlalchemy.orm import Session
from app.db.models import SystemLog


def create_system_log(db: Session, level: str, title: str, message: str) -> SystemLog:
    """Sistem olay günlüğünü veri tabanına kaydeder."""
    log = SystemLog(level=level, title=title, message=message)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_system_logs(db: Session, limit: int = 15) -> list[SystemLog]:
    """En güncel sistem olay günlüklerini tersten sıralı listeler."""
    return db.query(SystemLog).order_by(SystemLog.created_at.desc()).limit(limit).all()
