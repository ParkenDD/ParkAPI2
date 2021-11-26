from rest_framework import serializers, viewsets

from park_data.models import *
from .fields import *


class ParkingPoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParkingPool
        exclude = ["id"]

    date_created = DateTimeField()
    date_updated = DateTimeField()


class LatestParkingDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = LatestParkingData
        exclude = ["id"]

    timestamp = DateTimeField()
    lot_timestamp = DateTimeField()


class ParkingDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParkingData
        exclude = ["lot"]

    lot_id = LotField(source="lot", read_only=True)
    timestamp = DateTimeField()
    lot_timestamp = DateTimeField()


class ParkingLotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParkingLot
        exclude = ["id", "pool", "geo_point"]
        depth = 2  # include latest_data

    pool_id = PoolField(source="pool", read_only=True)
    coordinates = CoordField(source="geo_point", read_only=True)
    distance = DistanceField()
    latest_data = LatestParkingDataSerializer()
    date_created = DateTimeField()
    date_updated = DateTimeField()

