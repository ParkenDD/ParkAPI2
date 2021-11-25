from rest_framework import serializers, viewsets

from park_data.models import *


class PoolField(serializers.RelatedField):
    def to_representation(self, value):
        return value.pool_id


class LotField(serializers.RelatedField):
    def to_representation(self, value):
        return value.lot_id


class ParkingLotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParkingLot
        exclude = ["id", "pool"]

    pool_id = PoolField(source="pool", read_only=True)


class ParkingLotViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ParkingLot.objects.all()
    serializer_class = ParkingLotSerializer


# ----


class ParkingDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParkingData
        exclude = ["id", "lot"]

    lot_id = LotField(source="lot", read_only=True)


class ParkingDataViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ParkingData.objects.all()
    serializer_class = ParkingDataSerializer


