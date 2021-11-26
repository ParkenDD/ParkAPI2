from django_filters.rest_framework import DjangoFilterBackend

from park_data.models import *
from .serializers import *
from .filters import *


class GeoParkingLotViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ParkingLot.objects.all()
    serializer_class = ParkingLotSerializer
    filter_backends = [SpatialFilter, filters.OrderingFilter, DjangoFilterBackend]
    ordering_fields = ["lot_id", "pool_id", "max_capacity"]
    lookup_field = "lot_id"


class ParkingPoolViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ParkingPool.objects.all()
    serializer_class = ParkingPoolSerializer
    lookup_field = "pool_id"


# ----


class ParkingLotViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ParkingLot.objects.all()
    serializer_class = ParkingLotSerializer
    lookup_field = "lot_id"

# ----


class ParkingDataViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ParkingData.objects.all()
    serializer_class = ParkingDataSerializer

