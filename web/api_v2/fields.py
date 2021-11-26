import datetime

import pytz
from rest_framework import serializers, viewsets


class PoolField(serializers.RelatedField):
    def to_representation(self, value):
        return value.pool_id


class LotField(serializers.RelatedField):
    def to_representation(self, value):
        return value.lot_id


class CoordField(serializers.Field):
    def to_representation(self, value):
        return value.tuple


class DateTimeField(serializers.DateTimeField):

    def __init__(self, **kwargs):
        super().__init__(format="%Y-%m-%dT%H:%M:%SZ", **kwargs)


class DistanceField(serializers.Field):

    def __init__(self, **kwargs):
        super().__init__(read_only=True, allow_null=True, **kwargs)

    def to_representation(self, value):
        if not value:
            return None
        return round(value.km, 3)

