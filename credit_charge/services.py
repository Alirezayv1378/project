# services.py
import decimal
import logging

import rest_framework.exceptions
from django.db import transaction

import credit_charge.consts
import credit_charge.exceptions
import credit_charge.models

logger = logging.getLogger(__name__)


def create_charge(phone_number: str, amount: decimal.Decimal) -> credit_charge.models.Charge:
    try:
        user = credit_charge.models.User.objects.get(phone_number=phone_number)
    except credit_charge.models.User.DoesNotExist:
        raise rest_framework.exceptions.ValidationError("User with this phone number does not exist.")  # noqa: B904

    if not user.is_seller:
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
            credit_charge.models.User.update_balance(
                amount=decimal.Decimal("-1") * amount,
                phone_number=seller.phone_number,
            )
            credit_charge.models.User.update_balance(amount=amount, phone_number=receiver.phone_number)
            user_transaction.confirm_transaction()
    except credit_charge.exceptions.NegetavieBalanceError as e:
        logger.error(f"Seller {seller} has insufficient balance: {e}")
        user_transaction.reject_transaction(reason=credit_charge.consts.UserTransactionDescription.INSUFFICIENT_BALANCE)
    except Exception as e:
        logger.error(f"Error raised during updating {seller} and {receiver} wallet balance: {e}")
        user_transaction.reject_transaction(reason=credit_charge.consts.UserTransactionDescription.OTHER_REASONS)
    return user_transaction
