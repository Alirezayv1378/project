# services.py
import decimal
import logging

import rest_framework.exceptions
from django.db import models, transaction

import credit_charge.consts
import credit_charge.exceptions
import credit_charge.models

logger = logging.getLogger(__name__)


def create_charge(phone_number: str, amount: decimal.Decimal) -> credit_charge.models.Charge:
    try:
        user = credit_charge.models.User.objects.get(phone_number=phone_number)
    except credit_charge.models.User.DoesNotExist:
        raise rest_framework.exceptions.ValidationError("User with this phone number does not exist.")  # noqa: B904

    if user.role != credit_charge.consts.UserRoles.SELLER:
        raise rest_framework.exceptions.ValidationError("Only sellers are allowed to create charge request.")

    return credit_charge.models.Charge.create_charge(amount=amount, user=user)


def create_transaction(
    seller_phone_number: str,
    receiver_phone_number: str,
    amount: decimal.Decimal,
) -> credit_charge.models.UserTransaction:
    try:
        seller = credit_charge.models.User.objects.get(phone_number=seller_phone_number)
    except credit_charge.models.User.DoesNotExist:
        raise rest_framework.exceptions.ValidationError("Seller with this phone number does not exist.")  # noqa: B904

    try:
        receiver = credit_charge.models.User.objects.get(phone_number=receiver_phone_number)
    except credit_charge.models.User.DoesNotExist:
        raise rest_framework.exceptions.ValidationError("Receiver with this phone number does not exist.")  # noqa: B904

    if not seller.is_seller:
        raise rest_framework.exceptions.ValidationError("Only sellers are allowed to create transaction.")

    user_transaction = credit_charge.models.UserTransaction.create_transaction(
        seller=seller,
        receiver_user=receiver,
        amount=amount,
    )
    try:
        with transaction.atomic():
            seller.update_balance(amount=decimal.Decimal("-1") * amount, user=seller)
            receiver.update_balance(amount=amount, user=receiver)
    except credit_charge.exceptions.NegetavieBalanceError as e:
        logger.error(f"Seller {seller} has insufficient balance: {e}")
        user_transaction.reject_transaction(reason=credit_charge.consts.UserTransactionDescription.INSUFFICIENT_BALANCE)
    except Exception as e:
        logger.error(f"Error raised during updating {seller} and {receiver} wallet balance: {e}")
        user_transaction.reject_transaction(reason=credit_charge.consts.UserTransactionDescription.OTHER_REASONS)
    return user_transaction


def check_user_balance(user: credit_charge.models.User) -> None:
    try:
        total_charge = credit_charge.models.Charge.objects.filter(user=user).aggregate(total=models.Sum("amount"))
        total_expense = credit_charge.models.UserTransaction.objects.filter(receiver_user=user).aggregate(
            total=models.Sum("amount"),
        )
        diff = total_charge["total"] - total_expense["total"]
        if diff < 0:
            raise credit_charge.exceptions.UserBalanceCheckError(user=user, diff=diff)
    except credit_charge.models.Charge.DoesNotExist:
        pass
    except credit_charge.models.UserTransaction.DoesNotExist:
        pass
