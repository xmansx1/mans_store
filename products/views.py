# products/views.py
from decimal import Decimal, ROUND_HALF_UP
import logging
import requests  # لإرسال مباشر أثناء التطوير

from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import SellRequestForm
from .models import Product

# نحاول استيراد مرسلات تيليجرام (للإنتاج)
try:
    from .notify import (
        _send_telegram_message_sync,
        _send_telegram_document_sync,
        send_telegram_message_async,
        send_telegram_document_async,
    )
except Exception:
    def _send_telegram_message_sync(*args, **kwargs): return None  # type: ignore
    def _send_telegram_document_sync(*args, **kwargs): return None  # type: ignore
    def send_telegram_message_async(*args, **kwargs): return None  # type: ignore
    def send_telegram_document_async(*args, **kwargs): return None  # type: ignore

log = logging.getLogger(__name__)


# ===== أدوات مساعدة =====
def _money(value: Decimal) -> Decimal:
    return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _tg_send_direct(text: str, *, caption_path: str | None = None) -> None:
    """
    إرسال مباشر لتليجرام أثناء DEBUG=True فقط.
    يطبع نتيجة واضحة في الكونسول. لا يرمي أخطاء للمستخدم.
    """
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
    chat_id = getattr(settings, "TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        log.warning("Telegram DIRECT: missing token/chat_id")
        return

    # رسالة نصية
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            timeout=10,
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
        )
        if resp.status_code == 200:
            log.info("Telegram DIRECT sendMessage OK")
        else:
            log.error("Telegram DIRECT sendMessage FAILED %s: %s", resp.status_code, resp.text[:500])
    except Exception as exc:
        log.exception("Telegram DIRECT sendMessage exception: %s", exc)

    # وثيقة (اختياري)
    if caption_path:
        try:
            with open(caption_path, "rb") as f:
                resp2 = requests.post(
                    f"https://api.telegram.org/bot{token}/sendDocument",
                    timeout=15,
                    data={"chat_id": chat_id, "caption": "إثبات شراء"},
                    files={"document": (caption_path.split("/")[-1], f)},
                )
            if resp2.status_code == 200:
                log.info("Telegram DIRECT sendDocument OK")
            else:
                log.error("Telegram DIRECT sendDocument FAILED %s: %s", resp2.status_code, resp2.text[:500])
        except Exception as exc:
            log.exception("Telegram DIRECT sendDocument exception: %s", exc)


# ===== صفحة الهبوط =====
def landing_page(request):
    """
    صفحة الهبوط مع بحث/تصفية وترقيم صفحات.
    يدعم:
      - q: بحث نصي في الاسم/التفاصيل
      - category: تصفية بالتصنيف
      - max_price: سعر أقصى
      - sort: ترتيب (newest|price_asc|price_desc)
      - page: رقم الصفحة
    """
    q = (request.GET.get("q") or "").strip()
    category = (request.GET.get("category") or "").strip()
    max_price = (request.GET.get("max_price") or "").strip()
    sort = (request.GET.get("sort") or "newest").strip()

    qs = Product.objects.filter(is_active=True)

    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(details__icontains=q))
    if category:
        qs = qs.filter(category=category)
    if max_price:
        try:
            qs = qs.filter(price__lte=Decimal(max_price))
        except Exception:
            pass

    if sort == "price_asc":
        qs = qs.order_by("price", "-created_at")
    elif sort == "price_desc":
        qs = qs.order_by("-price", "-created_at")
    else:
        qs = qs.order_by("-created_at")

    paginator = Paginator(qs, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "landing.html", {
        "products": page_obj.object_list,
        "page_obj": page_obj,
        "paginator": paginator,
        "q": q,
        "category": category,
        "max_price": max_price,
        "sort": sort,
        "categories": Product.Category.choices,
    })


# ===== استقبال نموذج بيع الجهاز =====
def create_sell_request(request):
    """
    - يعيد احتساب المبلغ المستحق = 70% من سعر الشراء
    - يحفظ الطلب
    - يرسل تنبيه تيليجرام
    - يعيد التوجيه برسالة نجاح
    """
    if request.method != "POST":
        return HttpResponseBadRequest("Bad request")

    form = SellRequestForm(request.POST, request.FILES)
    if not form.is_valid():
        messages.error(request, "تحقق من الحقول وأعد المحاولة.")
        return redirect("landing")

    # المنتج من الخادم
    try:
        product = Product.objects.get(pk=form.cleaned_data["product"].pk)
    except Product.DoesNotExist:
        messages.error(request, "المنتج غير موجود.")
        return redirect("landing")

    # سعر الشراء + 70%
    try:
        raw_price = request.POST.get("purchase_price", product.price)
        purchase_price = _money(Decimal(str(raw_price)))
    except Exception:
        purchase_price = _money(Decimal(product.price))
    payout = _money(purchase_price * Decimal("0.70"))

    sr = form.save(commit=False)
    sr.purchase_price = purchase_price
    sr.payout_amount = payout
    sr.save()

    # نص التنبيه
    admin_url = request.build_absolute_uri(
        reverse("admin:products_sellrequest_change", args=[sr.id])
    )
    msg = (
        f"📨 <b>طلب بيع جهاز بعد الشراء</b>\n"
        f"— المنتج: <b>{product.name}</b>\n"
        f"— العميل: <b>{sr.customer_name}</b>\n"
        f"— جوال: <code>{sr.phone}</code>\n"
        f"— البنك: <b>{sr.bank_name}</b>\n"   # 👈 تمت الإضافة هنا
        f"— حساب: <code>{sr.account_number}</code>\n"
        f"— سعر الشراء: <b>{sr.purchase_price} ريال</b>\n"
        f"— المبلغ المستحق (بعد 30٪): <b>{sr.payout_amount} ريال</b>\n"
        f"— رقم العملية: <code>{sr.transaction_ref or '—'}</code>\n"
        f"— الإدارة: <a href=\"{admin_url}\">فتح في Django Admin</a>"
    )


    # إرسال مضمون:
    try:
        if settings.DEBUG:
            # تطوير: إرسال مباشر متزامن + لوق واضح
            _path = sr.proof_image.path if getattr(sr, "proof_image", None) and hasattr(sr.proof_image, "path") else None
            log.info("Telegram DIRECT try | CHAT_ID=%s TOKEN_PREFIX=%s", getattr(settings, "TELEGRAM_CHAT_ID", ""), str(getattr(settings, "TELEGRAM_BOT_TOKEN", ""))[:8])
            _tg_send_direct(msg, caption_path=_path)
        else:
            # إنتاج: عبر notify (غير متزامن)
            send_telegram_message_async(msg)
            if getattr(sr, "proof_image", None) and hasattr(sr.proof_image, "path"):
                send_telegram_document_async(sr.proof_image.path, caption=f"إثبات شراء — {product.name}")
    except Exception as exc:
        log.exception("Telegram notify error: %s", exc)

    messages.success(request, "تم إرسال الطلب بنجاح. سنقوم بالتواصل معك قريبًا.")
    return redirect("landing")
