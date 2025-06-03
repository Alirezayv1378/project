import rest_framework.routers

import credit_charge.views

router = rest_framework.routers.DefaultRouter()
router.register(r"charges", credit_charge.views.ChargeViewSet, basename="charge")
router.register(r"transactions", credit_charge.views.UserTransactionViewSet, basename="transaction")
router.register(r"users", credit_charge.views.UserViewSet, basename="user")

urlpatterns = router.urls
