import django.core.exceptions
from rest_framework import serializers

import credit_charge.model_validators
import credit_charge.models


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = credit_charge.models.User
        fields = ("phone_number", "balance", "is_seller")


class ChargeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=0, min_value=0)

    class Meta:
        model = credit_charge.models.Charge
        fields = ("user", "amount", "transaction_id", "status")
        read_only_fields = ("transaction_id", "status")


class UserTransactionSerializer(serializers.ModelSerializer):
    seller = UserSerializer(read_only=True)
    receiver_user = UserSerializer(read_only=True)

    receiver_phone_number = serializers.CharField(write_only=True, max_length=16)
    amount = serializers.DecimalField(max_digits=12, decimal_places=0, min_value=0)

    class Meta:
        model = credit_charge.models.UserTransaction
        fields = (
            "seller",
            "receiver_user",
            "receiver_phone_number",
            "amount",
            "status",
            "transaction_id",
            "description",
        )
        read_only_fields = (
            "seller",
            "receiver_user",
            "status",
            "transaction_id",
            "description",
        )

    def validate_receiver_phone_number(self, value):
        try:
            credit_charge.model_validators.validate_phone_number(value)
            return value
        except django.core.exceptions.ValidationError as e:
            raise serializers.ValidationError(e.message) from e
