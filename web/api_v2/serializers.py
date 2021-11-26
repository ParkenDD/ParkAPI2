from rest_framework import serializers, viewsets

from park_data.models import *


class PoolField(serializers.RelatedField):
    def to_representation(self, value):
        return value.pool_id


class LotField(serializers.RelatedField):
    def to_representation(self, value):
        return value.lot_id


class CoordField(serializers.Field):
    def to_representation(self, value):
        return value.tuple


class LatestParkingDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = LatestParkingData
        exclude = ["id"]


# ----


class ParkingPoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParkingPool
        exclude = ["id"]


class ParkingPoolViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ParkingPool.objects.all()
    serializer_class = ParkingPoolSerializer
    lookup_field = "pool_id"


# ----


class ParkingLotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParkingLot
        exclude = ["id", "pool", "geo_point"]
        depth = 2

    pool_id = PoolField(source="pool", read_only=True)
    coordinates = CoordField(source="geo_point", read_only=True)
    latest_data = LatestParkingDataSerializer()


class ParkingLotViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ParkingLot.objects.all()
    serializer_class = ParkingLotSerializer
    lookup_field = "lot_id"

# ----


class ParkingDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParkingData
        exclude = ["lot"]

    lot_id = LotField(source="lot", read_only=True)


class ParkingDataViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ParkingData.objects.all()
    serializer_class = ParkingDataSerializer

