import html as html_lib

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger("email_service")


def _config() -> ConnectionConfig:
    return ConnectionConfig(
        MAIL_USERNAME=settings.SMTP_USER,
        MAIL_PASSWORD=settings.SMTP_PASSWORD,
        MAIL_FROM=settings.SMTP_FROM,
        MAIL_PORT=settings.SMTP_PORT,
        MAIL_SERVER=settings.SMTP_HOST,
        MAIL_STARTTLS=True,
        MAIL_SSL_TLS=False,
        USE_CREDENTIALS=True,
    )


async def send_password_reset_email(to_email: str, full_name: str, token: str) -> None:
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.debug("SMTP not configured — şifre sıfırlama e-postası gönderilmedi")
        logger.info({"event": "dev_reset_token", "email": to_email, "token": token})
        return

    safe_name = html_lib.escape(full_name or "Kullanıcı")
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
      <h2 style="color: #0ea5b7;">Unilex AI — Şifre Sıfırlama</h2>
      <p>Merhaba {safe_name},</p>
      <p>Hesabınız için bir şifre sıfırlama talebi aldık. Aşağıdaki bağlantıya tıklayarak yeni şifrenizi belirleyebilirsiniz:</p>
      <p style="margin: 24px 0;">
        <a href="{reset_url}"
           style="background:#0ea5b7;color:white;padding:12px 24px;border-radius:8px;text-decoration:none;display:inline-block;font-weight:bold;">
          Şifremi Sıfırla
        </a>
      </p>
      <p>Bu bağlantı <b>30 dakika</b> süreyle geçerlidir.</p>
      <p style="color:#888;font-size:12px;">Bu talebi siz yapmadıysanız bu e-postayı yok sayabilirsiniz.</p>
    </div>
    """
    message = MessageSchema(
        subject="Unilex AI — Şifre Sıfırlama Talebi",
        recipients=[to_email],
        body=body,
        subtype=MessageType.html,
    )
    op = logger.start_operation("send_reset_email")
    op.add_field("email", to_email)
    try:
        await FastMail(_config()).send_message(message)
        op.succeed()
    except Exception:
        op.fail()
        raise
