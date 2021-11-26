from django.urls import path, include
from django.conf.urls import url
from rest_framework import routers

from . import views


router = routers.DefaultRouter()
router.register(r'pools', views.ParkingPoolViewSet)
#router.register(r'all-lots', views.ParkingLotViewSet)
#router.register(r'all-data', views.ParkingDataViewSet)
router.register(r'lots', views.GeoParkingLotViewSet)
#router.register(r'q', views.ParkingDataQueryView, basename="query")


urlpatterns = [
    path('', include(router.urls)),
    # path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]