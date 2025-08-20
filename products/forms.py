from django import forms
from .models import SellRequest

class SellRequestForm(forms.ModelForm):
    class Meta:
        model = SellRequest
        fields = ["product", "customer_name", "phone", "account_number", "bank_name", "proof_image", "transaction_ref"]
        widgets = {
            "product": forms.HiddenInput(),
            "purchase_price": forms.HiddenInput(),
            "payout_amount": forms.HiddenInput(),
        }

    def clean(self):
        data = super().clean()
        ref = (data.get("transaction_ref") or "").strip()
        img = data.get("proof_image")
        if not ref and not img:
            raise forms.ValidationError("يجب إرفاق صورة إثبات الشراء أو إدخال رقم  رقم الطلب.")
        return data
