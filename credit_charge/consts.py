from django.db import models
from django.utils.translation import gettext_lazy as _


class TransactionStatus(models.TextChoices):
    WAITING = "WAITING", _("در انتظار تأیید")
    CONFIRMED = "CONFIRMED", _("تأیید شده")
    FAILED = "FAILED", _("رد شده")


class UserTransactionDescription(models.TextChoices):
    INSUFFICIENT_BALANCE = "INSUFFICIENT_BALANCE", _("Insufficient Balance")
    OTHER_REASONS = "OTHER_REASONS", _("Other Reasons")
