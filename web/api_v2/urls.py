from django.urls import path, include
from rest_framework import routers

from .serializers import (
    ParkingDataViewSet,
    ParkingLotViewSet,
)

# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'lots', ParkingLotViewSet)
router.register(r'data', ParkingDataViewSet)


urlpatterns = [
    path('', include(router.urls)),
    # path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]