"""park_api URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView

from .views import stats

urlpatterns = [
    path("stats/", stats.StatsView.as_view(), name="stats"),
    path("admin/", admin.site.urls),
    path("api/", include('park_api.api_urls')),
    # Maintain API v1 compatibility by redirecting former URLs to new locations
    path("", RedirectView.as_view(url='api/')),
    path("<city>", RedirectView.as_view(url='api/%(city)s')),
    path("<city>/<lot_id>/timespan", RedirectView.as_view(url='api/v1/%(city)s/%(lot_id)s/timespan')),
]

if settings.DEBUG is True:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
