import logging

import rest_framework.response
from rest_framework import mixins, permissions, status, viewsets

import credit_charge.exceptions
import credit_charge.models
import credit_charge.serializers
import credit_charge.services

logger = logging.getLogger(__name__)


class IsSellerOrAuthenticated(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if view.action != "create":
            return user.is_authenticated
        return user.is_seller and user.is_authenticated


class UserViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = credit_charge.models.User.objects.all()
    serializer_class = credit_charge.serializers.UserSerializer
    lookup_field = "phone_number"


class ChargeViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = credit_charge.serializers.ChargeSerializer
    queryset = credit_charge.models.Charge.objects.all()
    lookup_field = "transaction_id"
    permission_classes = [IsSellerOrAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount = serializer.validated_data["amount"]
        try:
            charge = credit_charge.models.Charge.create_charge(user=request.user, amount=amount)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return rest_framework.response.Response(
                {"message": "Unexpected error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        response_serializer = self.get_serializer(charge)
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
    serializer_class = credit_charge.serializers.UserTransactionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        receiver_phone_number = serializer.validated_data["receiver_phone_number"]
        amount = serializer.validated_data["amount"]
        seller_phone_number = request.user.phone_number

        try:
            transaction = credit_charge.services.create_transaction(
                seller_phone_number=seller_phone_number,
                receiver_phone_number=receiver_phone_number,
                amount=amount,
            )
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return rest_framework.response.Response(
                {"message": "Unexpected error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        response_serializer = self.get_serializer(transaction)
        return rest_framework.response.Response(response_serializer.data, status=status.HTTP_201_CREATED)
