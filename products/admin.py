# products/admin.py
from django.contrib import admin
from .models import Product, SellRequest


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # اعرض معلومات المنتج الفعلية فقط
    list_display = ("name", "category", "price", "is_active", "created_at")
    list_filter = ("category", "is_active", "created_at")
    search_fields = ("name", "details")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    list_per_page = 25
    save_on_top = True


@admin.register(SellRequest)
class SellRequestAdmin(admin.ModelAdmin):
    # عرض شامل لطلبات البيع
    list_display = (
        "customer_name",
        "phone",
        "bank_name",
        "account_number",
        "product",
        "purchase_price",
        "payout_amount",
        "transaction_ref",
        "created_at",
    )
    # ملاحظة: لا نضع product__category هنا لأن list_filter لا يدعم سلاسل العلاقات مباشرة
    list_filter = ("product", "created_at")
    search_fields = ("customer_name", "phone", "bank_name", "transaction_ref")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    list_per_page = 25
    save_on_top = True
