from django.urls import path, include
from django.conf.urls import url
from rest_framework import routers

from .serializers import (
    ParkingDataViewSet,
    ParkingLotViewSet,
    ParkingPoolViewSet,
)

from . import views


router = routers.DefaultRouter()
router.register(r'all-pools', ParkingPoolViewSet)
router.register(r'all-lots', ParkingLotViewSet)
router.register(r'all-data', ParkingDataViewSet)
router.register(r'lots', views.GeoParkingLotViewSet)
#router.register(r'q', ParkingDataQueryView, basename="query")


urlpatterns = [
    path('', include(router.urls)),
    #path('q/', views.ParkingDataQueryView.as_view(), name="query")
    # path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]