from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _

class Product(models.Model):
    class Category(models.TextChoices):
        NEW = "جديد", _("جديد")
        USED = "مستعمل", _("مستعمل")
        GAMES = "ألعاب", _("ألعاب")
        COMPUTERS = "حواسيب", _("حواسيب")
        ACCESSORIES = "ملحقات", _("ملحقات")

    name = models.CharField(_("الاسم"), max_length=255)
    category = models.CharField(_("التصنيف"), max_length=20, choices=Category.choices, blank=True)
    badge = models.CharField(_("شارة البطاقة"), max_length=50, blank=True)
    price = models.DecimalField(_("السعر"), max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    details = models.TextField(_("التفاصيل"), blank=True)
    image = models.ImageField(_("الصورة"), upload_to="products/")
    store_url = models.URLField(_("رابط صفحة المنتج في المتجر"))
    is_active = models.BooleanField(_("نشط؟"), default=True)

    created_at = models.DateTimeField(_("أُنشئ في"), auto_now_add=True)
    updated_at = models.DateTimeField(_("عُدّل في"), auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = _("منتج")
        verbose_name_plural = _("منتجات")

    def __str__(self):
        return self.name


from django.core.validators import RegexValidator

class SellRequest(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="sell_requests")
    customer_name = models.CharField("اسم العميل", max_length=255)
    phone = models.CharField(
        "رقم الجوال", max_length=20,
        validators=[RegexValidator(r"^\+?\d{8,15}$", "رقم الجوال غير صحيح")]
    )
    account_number = models.CharField("رقم الحساب (نفس العميل)", max_length=34)  # IBAN أو رقم حساب
    bank_name = models.CharField(max_length=100)  
    transaction_ref = models.CharField("رقم العملية (اختياري)", max_length=100, blank=True)
    proof_image = models.ImageField("إرفاق صورة إثبات الشراء (اختياري)", upload_to="proofs/", blank=True)
    purchase_price = models.DecimalField("سعر الشراء", max_digits=10, decimal_places=2)
    payout_amount = models.DecimalField("المبلغ المستحق بعد 30%", max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "طلب بيع الجهاز بعد الشراء"
        verbose_name_plural = "طلبات بيع الجهاز بعد الشراء"

    def __str__(self):
        return f"{self.customer_name} - {self.product.name}"
