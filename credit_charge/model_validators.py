import re

from django.core.exceptions import ValidationError

import credit_charge.consts
import credit_charge.models


def validate_phone_number(value):
    """
    Validates phone numbers in formats like +989393292651 or 09393292651.
    Supports international (+[country code][number]) and local numbers.
    """
    # Remove any whitespace
    value = value.strip()

    pattern = r"^(?:\+[0-9]{7,15}|[0-9]{7,15})$"
    if not re.match(pattern, value):
        raise ValidationError("Enter a valid phone number.")


def validate_transaction_status(
    instance: "credit_charge.models.UserTransaction",
):
    previous_status = instance.tracker.previous("status")
    if previous_status == credit_charge.consts.TransactionStatus.WAITING or previous_status is None:
        return
    if previous_status != instance.status:
        raise ValidationError("Status cannot be changed.")


def validate_charge_status(
    instance: "credit_charge.models.Charge",
):
    previous_status = instance.tracker.previous("status")
    if previous_status == credit_charge.consts.TransactionStatus.WAITING or previous_status is None:
        return
    if previous_status != instance.status:
        raise ValidationError("Status cannot be changed.")
