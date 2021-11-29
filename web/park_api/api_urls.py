from django.urls import path, include
from django.conf import settings
from django.conf.urls import url

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
    path("auth/", include('rest_framework.urls')),
    path("v2/", include("api_v2.urls")),

    url(r'^docs/swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    url(r'^docs/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    url(r'^docs/redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
