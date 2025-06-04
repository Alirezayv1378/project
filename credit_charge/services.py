# services.py
import decimal
import logging

import rest_framework.exceptions
from django.db import transaction

import credit_charge.consts
import credit_charge.exceptions
import credit_charge.models

logger = logging.getLogger(__name__)


@transaction.atomic
def create_transaction(
    seller_phone_number: str,
    receiver_phone_number: str,
    amount: decimal.Decimal,
) -> credit_charge.models.UserTransaction:
    if amount <= 0:
        raise rest_framework.exceptions.ValidationError("Amount must be greater than 0.")

    users = credit_charge.models.User.objects.select_for_update(of=["self"]).filter(
        phone_number__in=[seller_phone_number, receiver_phone_number],
    )
    users_by_phone = {user.phone_number: user for user in users}

    seller = users_by_phone.get(seller_phone_number)
    receiver = users_by_phone.get(receiver_phone_number)
    if seller is None:
        raise rest_framework.exceptions.ValidationError("Seller with this phone number does not exist.")
    if receiver is None:
        raise rest_framework.exceptions.ValidationError("Receiver with this phone number does not exist.")
    if not seller.is_seller:
        raise rest_framework.exceptions.ValidationError("Only sellers are allowed to create transaction.")

    user_transaction = credit_charge.models.UserTransaction.create_transaction(
        seller=seller,
        receiver_user=receiver,
        amount=amount,
    )
    try:
        seller.update_balance(amount=decimal.Decimal("-1") * amount)
        receiver.update_balance(amount=amount)
        user_transaction.confirm_transaction()
    except credit_charge.exceptions.NegetavieBalanceError:
        user_transaction.reject_transaction(reason=credit_charge.consts.UserTransactionDescription.INSUFFICIENT_BALANCE)
    except Exception as e:
        logger.error(f"Error raised during updating {seller} and {receiver} wallet balance: {e}")
        user_transaction.reject_transaction(reason=credit_charge.consts.UserTransactionDescription.OTHER_REASONS)
    return user_transaction
