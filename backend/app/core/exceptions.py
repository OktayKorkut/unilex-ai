"""
Unilex AI — merkezi exception sistemi.

dqa-backend'deki CustomException / add_exception_handler pattern'ından esinlenilmiştir.
"""

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.requests import Request

from app.core.logger import get_logger

logger = get_logger("exceptions")


# ---------------------------------------------------------------------------
# Hata kodları ve mesajları
# ---------------------------------------------------------------------------

class ErrorCodes:
    INTERNAL_ERROR            = "UNILEX_001"
    UNIVERSITY_NOT_FOUND      = "UNILEX_002"
    SESSION_NOT_FOUND         = "UNILEX_003"
    CRAWL_FAILED              = "UNILEX_004"
    EMBED_FAILED              = "UNILEX_005"
    CHAT_ERROR                = "UNILEX_006"
    VALIDATION_ERROR          = "UNILEX_007"
    UNIVERSITY_DETECT_FAILED  = "UNILEX_008"
    MESSAGE_NOT_FOUND         = "UNILEX_009"


class ErrorMessages:
    INTERNAL_ERROR            = "Beklenmeyen bir hata oluştu."
    UNIVERSITY_NOT_FOUND      = "Üniversite bulunamadı."
    SESSION_NOT_FOUND         = "Oturum bulunamadı veya bu oturuma erişim yetkiniz yok."
    CRAWL_FAILED              = "Mevzuat sayfası taranamadı."
    EMBED_FAILED              = "Belgeler işlenemedi."
    CHAT_ERROR                = "Sohbet isteği işlenemedi."
    VALIDATION_ERROR          = "İstek doğrulaması başarısız."
    UNIVERSITY_DETECT_FAILED  = "Hangi üniversite hakkında bilgi almak istediğinizi anlayamadım."
    MESSAGE_NOT_FOUND         = "Mesaj bulunamadı veya bu mesaja erişim yetkiniz yok."


# ---------------------------------------------------------------------------
# Temel exception sınıfı
# ---------------------------------------------------------------------------

class UnilexException(Exception):
    """
    Uygulamaya özgü temel exception.

    Args:
        code: Hata kodu (ErrorCodes sabiti)
        message: İnsan tarafından okunabilir hata mesajı
        status_code: HTTP durum kodu (varsayılan 400)
        parameters: Ek bağlam parametreleri
    """

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        parameters: list | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.parameters = parameters
        super().__init__(message)

    def __str__(self) -> str:
        return self.message


# ---------------------------------------------------------------------------
# Domain-specific exception sınıfları
# ---------------------------------------------------------------------------

class UniversityNotFoundError(UnilexException):
    def __init__(self) -> None:
        super().__init__(
            code=ErrorCodes.UNIVERSITY_NOT_FOUND,
            message=ErrorMessages.UNIVERSITY_NOT_FOUND,
            status_code=404,
        )


class SessionNotFoundError(UnilexException):
    def __init__(self) -> None:
        super().__init__(
            code=ErrorCodes.SESSION_NOT_FOUND,
            message=ErrorMessages.SESSION_NOT_FOUND,
            status_code=404,
        )


class CrawlFailedError(UnilexException):
    def __init__(self, detail: str = "") -> None:
        super().__init__(
            code=ErrorCodes.CRAWL_FAILED,
            message=f"{ErrorMessages.CRAWL_FAILED} {detail}".strip(),
            status_code=500,
        )


class EmbedFailedError(UnilexException):
    def __init__(self) -> None:
        super().__init__(
            code=ErrorCodes.EMBED_FAILED,
            message=ErrorMessages.EMBED_FAILED,
            status_code=500,
        )


class ChatError(UnilexException):
    def __init__(self, detail: str = "") -> None:
        super().__init__(
            code=ErrorCodes.CHAT_ERROR,
            message=f"{ErrorMessages.CHAT_ERROR} {detail}".strip(),
            status_code=500,
        )


class MessageNotFoundError(UnilexException):
    def __init__(self) -> None:
        super().__init__(
            code=ErrorCodes.MESSAGE_NOT_FOUND,
            message=ErrorMessages.MESSAGE_NOT_FOUND,
            status_code=404,
        )


# ---------------------------------------------------------------------------
# Global exception handler kaydı
# ---------------------------------------------------------------------------

def add_exception_handler(app: FastAPI) -> None:
    """
    FastAPI uygulamasına uygulama genelinde exception handler'ları ekler.
    main.py'de app oluşturulduktan hemen sonra çağrılmalıdır.
    """

    @app.exception_handler(UnilexException)
    async def unilex_exception_handler(request: Request, exc: UnilexException) -> JSONResponse:
        logger.error(
            {"event": "unilex_exception", "code": exc.code, "message": exc.message},
            exc_info=False,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_code": exc.code,
                "message": exc.message,
                "parameters": exc.parameters,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        logger.error(
            {"event": "validation_error", "detail": str(exc)},
            exc_info=False,
        )
        return JSONResponse(
            status_code=422,
            content={
                "error_code": ErrorCodes.VALIDATION_ERROR,
                "message": ErrorMessages.VALIDATION_ERROR,
                "parameters": None,
            },
        )

    @app.exception_handler(Exception)
    async def unexpected_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error({"event": "unexpected_error", "detail": str(exc)})
        return JSONResponse(
            status_code=500,
            content={
                "error_code": ErrorCodes.INTERNAL_ERROR,
                "message": ErrorMessages.INTERNAL_ERROR,
                "parameters": None,
            },
        )
