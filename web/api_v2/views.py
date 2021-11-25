from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Distance
from rest_framework import serializers, viewsets, filters
from rest_framework.compat import coreapi, coreschema, distinct
from django_filters.rest_framework import DjangoFilterBackend

from park_data.models import *
from .serializers import ParkingLotSerializer, ParkingDataSerializer
from .filters import SpatialFilter


class GeoParkingLotViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ParkingLot.objects.all()
    serializer_class = ParkingLotSerializer
    filter_backends = [SpatialFilter, filters.OrderingFilter, DjangoFilterBackend]
    ordering_fields = ["lot_id", "pool_id", "max_capacity"]
    lookup_field = "lot_id"

    def get_serializer_context(self):
        super().get_serializer_context()
