from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular import views as drf_spectacular_views
from rest_framework_simplejwt import views as simplejwtviews

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/schema/", drf_spectacular_views.SpectacularAPIView.as_view(), name="schema"),
    path("api/v1/docs/", drf_spectacular_views.SpectacularSwaggerView.as_view(url_name="schema"), name="redoc"),
    path("api/v1/token/", simplejwtviews.TokenObtainPairView.as_view(), name="api_token_auth"),
    path("api/v1/token/refresh/", simplejwtviews.TokenRefreshView.as_view(), name="token_refresh"),
    path("api/v1/", include("credit_charge.urls")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
