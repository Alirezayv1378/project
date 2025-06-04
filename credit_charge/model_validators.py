import re

import django.core.exceptions

import credit_charge.consts
import credit_charge.models


def validate_phone_number(value):
    value = value.strip()

    pattern = r"^(?:\+[0-9]{7,15}|[0-9]{7,15})$"
    if not re.match(pattern, value):
        raise django.core.exceptions.ValidationError("Enter a valid phone number.")


def validate_transaction_status(
    instance: "credit_charge.models.UserTransaction",
):
    previous_status = instance.tracker.previous("status")
    if previous_status == credit_charge.consts.TransactionStatus.WAITING or previous_status is None:
        return
    if previous_status != instance.status:
        raise django.core.exceptions.ValidationError("Status cannot be changed.")


def validate_charge_status(
    instance: "credit_charge.models.Charge",
):
    previous_status = instance.tracker.previous("status")
    if previous_status == credit_charge.consts.TransactionStatus.WAITING or previous_status is None:
        return
    if previous_status != instance.status:
        raise django.core.exceptions.ValidationError("Status cannot be changed.")
