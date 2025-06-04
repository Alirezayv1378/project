import rest_framework.response
from rest_framework import mixins, permissions, status, viewsets

import credit_charge.exceptions
import credit_charge.models
import credit_charge.serializers
import credit_charge.services


class IsSellerOrAuthenticated(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if view.action != "create":
            return user.is_authenticated
        return user.is_seller and user.is_authenticated


class UserViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = credit_charge.models.User.objects.all()
    serializer_class = credit_charge.serializers.UserSerializer
    lookup_field = "id"


class ChargeViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = credit_charge.models.Charge.objects.all()
    lookup_field = "transaction_id"
    permission_classes = [IsSellerOrAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return credit_charge.serializers.CreateChargeRequestSerializer
        return credit_charge.serializers.ChargeSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid()
        charge = credit_charge.services.create_charge(
            phone_number=serializer.validated_data["phone_number"],
            amount=serializer.validated_data["amount"],
        )
        response_serializer = credit_charge.serializers.ChargeSerializer(charge)
        return rest_framework.response.Response(response_serializer.data, status=status.HTTP_201_CREATED)


class UserTransactionViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = credit_charge.models.UserTransaction.objects.all()
    lookup_field = "transaction_id"
    permission_classes = [IsSellerOrAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return credit_charge.serializers.CeateUserTransactionRequestSerializer
        return credit_charge.serializers.UserTransactionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid()

        try:
            transaction = credit_charge.services.create_transaction(
                seller_phone_number=serializer.validated_data["seller_phone_number"],
                receiver_phone_number=serializer.validated_data["receiver_phone_number"],
                amount=serializer.validated_data["amount"],
            )
        except credit_charge.exceptions.UserBalanceCheckError as e:
            return rest_framework.response.Response(
                {
                    "message": "Insufficient balance",
                    "user": str(e.user),
                    "diff": str(e.diff),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        response_serializer = credit_charge.serializers.UserTransactionSerializer(transaction)
        return rest_framework.response.Response(response_serializer.data, status=status.HTTP_201_CREATED)
