import decimal
import logging
import uuid

import model_utils
from django.core import exceptions
from django.db import models
from django.utils.translation import gettext_lazy as _

import credit_charge.consts
import credit_charge.exceptions
import credit_charge.model_validators
import utils.consts
import utils.models

logger = logging.getLogger(__name__)


class User(utils.models.CreateUpdateTracker):
    phone_number = models.CharField(
        **utils.consts.nbfalse,
        max_length=16,
        unique=True,
        verbose_name=_("شماره موبایل"),
        validators=[credit_charge.model_validators.validate_phone_number],
    )
    balance = models.DecimalField(
        **utils.consts.nbfalse,
        verbose_name=_("بالانس حساب کاربر"),
        help_text=_("تومان"),
        max_digits=12,
        decimal_places=0,
        default=0,
    )
    is_seller = models.BooleanField(
        **utils.consts.nbfalse,
        verbose_name=_("فروشنده"),
        default=False,
    )

    def __str__(self) -> str:
        return str(self.phone_number)

    class Meta:
        verbose_name = _("کاربر")
        verbose_name_plural = _("کاربران")

    @classmethod
    def update_balance(
        cls,
        amount: decimal.Decimal,
        phone_number: str,
    ):
        try:
            # Lock user object to prevent double-spending and race conditions
            user = cls.objects.select_for_update(of=["self"]).get(phone_number=phone_number)
            initial_balance = user.balance
            user.balance += amount
            if user.balance < 0:
                raise credit_charge.exceptions.NegetavieBalanceError(
                    amount=amount,
                    user=user,
                    user_balance=initial_balance,
                )
            user.save()
        except credit_charge.exceptions.NegetavieBalanceError as e:
            logger.error(f"User {user} has insufficient balance: {e}")
            raise e
        except exceptions.ObjectDoesNotExist as e:
            logger.error(f"User with phone number {phone_number} does not exist: {e}")
        except Exception as e:
            logger.error(f"Error raised during updating {user} wallet balance: {e}")
            raise e


class Charge(utils.models.CreateUpdateTracker):
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        **utils.consts.nbfalse,
        related_name="charges",
        verbose_name=_("کاربر"),
    )
    status = models.CharField(
        max_length=16,
        **utils.consts.nbfalse,
        choices=credit_charge.consts.TransactionStatus,
        default=credit_charge.consts.TransactionStatus.WAITING,
        verbose_name=_("وضعیت تراکنش"),
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        **utils.consts.nbfalse,
        verbose_name=_("مقدار شارژ حساب"),
        help_text=_("تومان"),
    )

    transaction_id = models.UUIDField(
        **utils.consts.nbfalse,
        verbose_name=_("شناسه شارژ"),
        unique=True,
    )

    tracker = model_utils.FieldTracker()

    class Meta:
        verbose_name = _("شارژ حساب")
        verbose_name_plural = _("شارژ حساب‌ها")

    def __str__(self) -> str:
        return f"{self.user} - {self.status}"

    @classmethod
    def create_charge(cls, amount: decimal.Decimal, user: User) -> "Charge":
        charge = cls.objects.create(
            user=user,
            amount=amount,
            status=credit_charge.consts.TransactionStatus.WAITING,
            transaction_id=uuid.uuid4(),
        )
        return charge

    def confirm_charge(self):
        self.status = credit_charge.consts.TransactionStatus.CONFIRMED
        self.save()

    def reject_charge(self):
        self.status = credit_charge.consts.TransactionStatus.FAILED
        self.save()

    def clean(self, **kwargs):
        credit_charge.model_validators.validate_charge_status(self)
        return super().clean(**kwargs)

    def save(self, **kwargs):
        self.full_clean()
        return super().save(**kwargs)


class UserTransaction(utils.models.CreateUpdateTracker):
    seller = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        **utils.consts.nbfalse,
        related_name="sender_payments",
        verbose_name=_("فروشنده"),
    )
    receiver_user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        **utils.consts.nbfalse,
        related_name="receiver_payments",
        verbose_name=_("کاربر دریافت کننده"),
    )
    transaction_id = models.UUIDField(
        **utils.consts.nbfalse,
        verbose_name=_("کد پیگیری"),
        unique=True,
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        **utils.consts.nbfalse,
        verbose_name=_("مقدار شارژ حساب"),
        help_text=_("تومان"),
    )
    status = models.CharField(
        max_length=16,
        **utils.consts.nbfalse,
        choices=credit_charge.consts.TransactionStatus,
        default=credit_charge.consts.TransactionStatus.WAITING,
        verbose_name=_("وضعیت تراکنش"),
    )
    description = models.CharField(
        **utils.consts.nbtrue,
        verbose_name=_("توضیحات"),
        max_length=32,
        choices=credit_charge.consts.UserTransactionDescription,
    )

    tracker = model_utils.FieldTracker()

    class Meta:
        verbose_name = _("تراکنش بین کاربران")
        verbose_name_plural = _("تراکنش‌های بین کاربران")

    @classmethod
    def create_transaction(cls, amount: decimal.Decimal, receiver_user: User, seller: User) -> "UserTransaction":
        transaction = cls.objects.create(
            amount=amount,
            receiver_user=receiver_user,
            seller=seller,
            status=credit_charge.consts.TransactionStatus.WAITING,
            transaction_id=uuid.uuid4(),
        )
        return transaction

    def confirm_transaction(self):
        self.status = credit_charge.consts.TransactionStatus.CONFIRMED
        self.save()

    def reject_transaction(self, reason: credit_charge.consts.UserTransactionDescription):
        self.status = credit_charge.consts.TransactionStatus.FAILED
        self.description = reason
        self.save()

    def clean(self, **kwargs):
        credit_charge.model_validators.validate_transaction_status(self)
        return super().full_clean(**kwargs)

    def save(self, **kwargs):
        self.clean()
        return super().save(**kwargs)
