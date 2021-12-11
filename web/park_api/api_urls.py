from django.urls import path, re_path, include
from django.conf import settings

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="ParkAPI",
        default_version='v1',
        description="ParkAPI documentation",
        #terms_of_service="",
        #contact=openapi.Contact(email=""),
        #license=openapi.License(name=""),
    ),
    public=True,
    permission_classes=(permissions.AllowAny, ),
)

urlpatterns = [
    # path("auth/", include('rest_framework.urls')),

    re_path('^docs/swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path('^docs/?$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path('^docs/redoc/?$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    path("v2/", include("api_v2.urls")),
    path("", include("api_v1.urls")),
]
