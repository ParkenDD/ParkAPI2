from django.urls import path, re_path, include
from django.conf.urls import url

from . import views

app_name = "api_v1"

urlpatterns = [
    path("", views.CityMapView.as_view(), name="city-map"),
    re_path("^status/?$", views.StatusView.as_view(), name="status"),
    re_path("^coffee/?$", views.CoffeeView.as_view(), name="coffee"),
    path("<slug:city>", views.CityLotsView.as_view(), name="city-lots"),
]