# products/notify.py
from __future__ import annotations
import logging
import threading
import requests
from django.conf import settings

log = logging.getLogger(__name__)

TG_SEND_MSG_URL = "https://api.telegram.org/bot{token}/sendMessage"
TG_SEND_DOC_URL = "https://api.telegram.org/bot{token}/sendDocument"


def _have_creds() -> bool:
    """تأكد من وجود بيانات تيليجرام الأساسية."""
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
    chat_id = getattr(settings, "TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        log.warning("Telegram creds missing (token/chat_id). Skipping notify.")
        return False
    return True


def _send_telegram_message_sync(text: str, parse_mode: str = "HTML") -> None:
    """
    إرسال متزامن لرسالة نصية — مفيد جدًا أثناء التطوير أو عند الحاجة لضمان الوصول.
    لا يرمي أخطاء للمستخدم؛ يسجلها في اللوج فقط.
    """
    if not _have_creds():
        return

    url = TG_SEND_MSG_URL.format(token=settings.TELEGRAM_BOT_TOKEN)
    try:
        resp = requests.post(
            url,
            timeout=10,
            json={
                "chat_id": settings.TELEGRAM_CHAT_ID,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True,
            },
        )
        if resp.status_code == 200:
            log.info("Telegram sendMessage OK.")
        else:
            log.error("Telegram sendMessage FAILED %s: %s", resp.status_code, resp.text[:500])
    except Exception as e:
        log.exception("Telegram sendMessage exception: %s", e)


def _send_telegram_document_sync(file_path: str, caption: str = "") -> None:
    """
    إرسال متزامن لوثيقة/صورة إثبات الشراء.
    """
    if not _have_creds():
        return

    url = TG_SEND_DOC_URL.format(token=settings.TELEGRAM_BOT_TOKEN)
    try:
        with open(file_path, "rb") as f:
            resp = requests.post(
                url,
                timeout=20,
                data={"chat_id": settings.TELEGRAM_CHAT_ID, "caption": caption},
                files={"document": (file_path.split("/")[-1], f)},
            )
        if resp.status_code == 200:
            log.info("Telegram sendDocument OK.")
        else:
            log.error("Telegram sendDocument FAILED %s: %s", resp.status_code, resp.text[:500])
    except Exception as e:
        log.exception("Telegram sendDocument exception: %s", e)


def send_telegram_message_async(text: str, parse_mode: str = "HTML") -> None:
    """
    تشغيل إرسال الرسالة في خيط مستقل حتى لا يعلّق طلب المستخدم (مناسب للإنتاج).
    في التطوير يمكنك استدعاء _send_telegram_message_sync مباشرةً من الـ view.
    """
    th = threading.Thread(
        target=_send_telegram_message_sync,
        args=(text, parse_mode),
        daemon=True,
    )
    th.start()


def send_telegram_document_async(file_path: str, caption: str = "") -> None:
    """
    تشغيل إرسال الوثيقة في خيط مستقل (مناسب للإنتاج).
    """
    th = threading.Thread(
        target=_send_telegram_document_sync,
        args=(file_path, caption),
        daemon=True,
    )
    th.start()
