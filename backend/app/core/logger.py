"""
Unilex AI — structured JSON logging.

dqa-backend'deki DocQALogger / OperationLog pattern'ından esinlenilmiştir.
Harici bağımlılık gerektirmez; Python stdlib logging kullanır.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any


class _JsonFormatter(logging.Formatter):
    """Her log kaydını tek satır JSON olarak biçimlendirir."""

    def format(self, record: logging.LogRecord) -> str:
        base: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "level": record.levelname,
            "logger": record.name,
        }
        msg = record.getMessage()
        try:
            parsed = json.loads(msg)
            if isinstance(parsed, dict):
                base.update(parsed)
            else:
                base["message"] = msg
        except (ValueError, TypeError):
            base["message"] = msg

        if record.exc_info:
            base["exception"] = self.formatException(record.exc_info)

        return json.dumps(base, ensure_ascii=False, default=str)


def _get_stdlib_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(f"unilex.{name}")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(_JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
    return logger


class OperationLog:
    """
    Tek bir işlemin yaşam döngüsünü ve meta verilerini takip eder.

    Kullanım:
        op = logger.start_operation("send_message")
        op.add_field("session_id", 42)
        op.succeed()   # veya  op.fail()
    """

    def __init__(self, operation_name: str, logger: logging.Logger) -> None:
        self._start = datetime.now()
        self._logger = logger
        self._fields: dict[str, Any] = {
            "operation_name": operation_name,
            "context_id": str(uuid.uuid4()),
        }

    def add_field(self, key: str, value: Any) -> "OperationLog":
        self._fields[key] = value
        return self

    def _snapshot(self, status: str) -> dict[str, Any]:
        elapsed = round((datetime.now() - self._start).total_seconds() * 1000, 2)
        return {**self._fields, "status": status, "duration_ms": elapsed}

    def succeed(self) -> None:
        self._logger.info(
            json.dumps(self._snapshot("succeeded"), ensure_ascii=False, default=str)
        )

    def fail(self, exc_info: bool = True) -> None:
        self._logger.error(
            json.dumps(self._snapshot("failed"), ensure_ascii=False, default=str),
            exc_info=exc_info,
        )

    def debug(self) -> None:
        self._logger.debug(
            json.dumps(self._snapshot("debugging"), ensure_ascii=False, default=str)
        )


class UnilexLogger:
    """
    dqa-backend DocQALogger API'siyle uyumlu ince sarmalayıcı.
    Her modül kendi named logger'ını alır.
    """

    def __init__(self, name: str) -> None:
        self._logger = _get_stdlib_logger(name)

    def _serialize(self, msg: Any) -> str:
        if isinstance(msg, dict):
            return json.dumps(msg, ensure_ascii=False, default=str)
        return str(msg)

    def info(self, msg: Any) -> None:
        self._logger.info(self._serialize(msg))

    def debug(self, msg: Any) -> None:
        self._logger.debug(self._serialize(msg))

    def error(self, msg: Any, exc_info: bool = True) -> None:
        self._logger.error(self._serialize(msg), exc_info=exc_info)

    def start_operation(self, operation_name: str) -> OperationLog:
        return OperationLog(operation_name, self._logger)


def get_logger(name: str) -> UnilexLogger:
    """Her modülden çağrılacak factory fonksiyonu."""
    return UnilexLogger(name)
