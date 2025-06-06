import logging

from django.contrib import admin, messages
from django.contrib.auth import admin as auth_admin
from django.db import models, transaction

import credit_charge.models

logger = logging.getLogger(__name__)


@admin.action(description="تأیید درخواست شارژ‌های انتخاب شده")
@transaction.atomic
def confirm_charges_action(
    modeladmin,
    request,
    queryset: models.QuerySet[credit_charge.models.Charge],
):
    try:
        for charge in queryset.select_related("user").select_for_update(of=["user"]):
            charge.user.update_balance(amount=charge.amount)
            charge.confirm_charge()

        modeladmin.message_user(request, "تراکنش‌ها با موفقیت تأیید شدند.", level=messages.SUCCESS)

    except Exception as e:
        logger.error(f"Error raised during confirming charges: {e}")
        modeladmin.message_user(request, f"خطا هنگام تأیید تراکنش‌ها: {e}", level=messages.ERROR)


@admin.action(description="رد درخواست شارژهای انتخاب شده")
@transaction.atomic
def reject_charges_action(
    modeladmin,
    request,
    queryset: models.QuerySet[credit_charge.models.Charge],
):
    try:
        for charge in queryset:
            charge.reject_charge()

        modeladmin.message_user(request, "تراکنش‌ها با موفقیت رد شدند.", level=messages.SUCCESS)

    except Exception as e:
        logger.error(f"Error raised during rejecting charges: {e}")
        modeladmin.message_user(request, f"خطا هنگام رد تراکنش‌ها: {e}", level=messages.ERROR)


@admin.register(credit_charge.models.User)
class UserAdmin(auth_admin.UserAdmin):
    fieldsets = (
        (None, {"fields": ("phone_number", "balance", "username", "password")}),
        ("Permissions", {"fields": ("is_superuser", "is_staff", "is_active", "is_seller")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("phone_number", "username", "password1", "password2", "is_seller"),
            },
        ),
    )
    list_display = ("phone_number", "balance", "is_seller", "is_staff", "is_superuser")
    search_fields = ("phone_number",)
    readonly_fields = ("balance",)
    list_filter = ("is_seller", "is_staff", "is_superuser")


@admin.register(credit_charge.models.Charge)
class ChargeAdmin(admin.ModelAdmin):
    actions = [confirm_charges_action, reject_charges_action]
    readonly_fields = ("user", "amount", "transaction_id", "status")
    list_display = ("user", "amount", "transaction_id", "status")
    search_fields = ("user", "transaction_id")
    list_filter = ("status",)


@admin.register(credit_charge.models.UserTransaction)
class UserTransactionAdmin(admin.ModelAdmin):
    readonly_fields = ("seller", "receiver_user", "amount", "status", "transaction_id")
    list_display = ("seller", "receiver_user", "amount", "status")
    search_fields = ("seller", "receiver_user", "transaction_id")
    list_filter = ("status",)
