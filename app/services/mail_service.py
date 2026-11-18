import logging
import smtplib
import ssl
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_password_reset(email: str, link: str) -> None:
    message = EmailMessage()
    message["Subject"] = "Восстановление пароля StudyAI"
    message["From"] = settings.smtp_from
    message["To"] = email
    message.set_content(
        f"Чтобы задать новый пароль, откройте ссылку:\n{link}\n\n"
        "Ссылка действует 30 минут и используется один раз.\n"
        "Если вы не запрашивали смену пароля, просто проигнорируйте письмо."
    )
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            if settings.smtp_starttls:
                smtp.starttls(context=ssl.create_default_context())
            if settings.smtp_username:
                smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(message)
    except (OSError, smtplib.SMTPException):
        logger.error("Password reset email could not be delivered")
