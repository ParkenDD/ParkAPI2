from django.urls import path, include
from django.conf.urls import url

from . import views

app_name = "api_v1"

urlpatterns = [
    path("", views.CityMapView.as_view(), name="city-map-view"),
    path("<slug:city>", views.CityView.as_view(), name="city-view"),
]