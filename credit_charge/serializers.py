from rest_framework import serializers

import credit_charge.models


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = credit_charge.models.User
        fields = ("id", "phone_number", "balance", "is_seller")


class ChargeSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = credit_charge.models.Charge
        fields = ("user", "amount", "transaction_id", "status")


class UserTransactionSerializer(serializers.ModelSerializer):
    seller = UserSerializer()
    receiver_user = UserSerializer()
    class Meta:
        model = credit_charge.models.UserTransaction
        fields = ("seller", "receiver_user", "amount", "status", "transaction_id", "description")


class CreateChargeRequestSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=16)
    amount = serializers.DecimalField(max_digits=12, decimal_places=0)

    def validate_phone_number(self, value):
        # Add more complex validation if needed
        if not credit_charge.models.User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("User with this phone number does not exist.")
        return value


class CeateUserTransactionRequestSerializer(serializers.Serializer):
    seller_phone_number = serializers.CharField(max_length=16)
    receiver_phone_number = serializers.CharField(max_length=16)
    amount = serializers.DecimalField(max_digits=12, decimal_places=0)

    def validate_seller_phone_number(self, value):
        if not credit_charge.models.User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("Seller with this phone number does not exist.")
        return value

    def validate_receiver_phone_number(self, value):
        if not credit_charge.models.User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("Receiver with this phone number does not exist.")
        return value
