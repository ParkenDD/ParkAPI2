import datetime
from typing import Tuple

from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _
from django.db.models import QuerySet

from rest_framework import (
    views, renderers, generics, parsers, fields, serializers, pagination,
    exceptions, versioning
)
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.schemas.openapi import AutoSchema
import coreapi
import coreschema

from locations.models import Location
from park_data.models import ParkingLot, ParkingPool, ParkingData, ParkingLotState


class ParkingDataV1Serializer(serializers.ModelSerializer):
    class Meta:
        model = ParkingData
        fields = ["timestamp", "free"]

    free = fields.IntegerField(source="num_free", read_only=True)


class TimespanVersioning(versioning.QueryParameterVersioning):
    default_version = "1.0"
    allowed_versions = ["1.0", "1.1"]
    version_param = "version"
    invalid_version_message = _("Error 400: invalid API version, expecting one of '1.0', '1.1'")


class TimestampV1Pagination(pagination.BasePagination):

    TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S"

    def paginate_queryset(self, queryset, request, view=None):
        date_from, date_to = self.get_timestamp_range(request)
        return (
            # Note: original api did timestamp > date_from instead of >=
            queryset.filter(timestamp__gte=date_from, timestamp__lt=date_to)
        )

    def get_paginated_response(self, data):
        return Response({
            "data": data
        })

    def get_timestamp_range(self, request: Request) -> Tuple[datetime.datetime, datetime.datetime]:
        try:
            params = request.query_params
            date_from = datetime.datetime.strptime(params["from"], self.TIMESTAMP_FORMAT)
            date_to = datetime.datetime.strptime(params["to"], self.TIMESTAMP_FORMAT)
        except:
            raise exceptions.ParseError(_(
                "Error 400: 'from' and/or 'to' URL params "
                "are not in ISO format, e.g. 2015-06-26T18:00:00"
            ))

        if (date_to - date_from) > datetime.timedelta(days=7):
            raise exceptions.ParseError(_(
                "Error 400: Time ranges cannot be greater than 7 days. "
                "To retrieve more data check out the dumps at https://parkendd.de/dumps"
            ))

        return date_from, date_to

    def get_paginated_response_schema(self, schema):
        return {
            'type': 'object',
            'properties': {
                'data': schema,
            },
        }

    def get_schema_fields(self, view):
        return [
            coreapi.Field(
                name="from",
                required=True,
                location='query',
                schema=coreschema.String(
                    title=force_str(_("from")),
                    description=force_str(_("Return data since this timestamp, in iso-format")),
                    pattern=r"\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d"
                )
            ),
            coreapi.Field(
                name="to",
                required=True,
                location='query',
                schema=coreschema.String(
                    title=force_str(_("to")),
                    description=force_str(_("Return data before this timestamp, in iso-format")),
                    pattern=r"\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d"
                )
            ),
            # Note: for simplicity attach the version parameter here instead of
            #   overloading the view's Schema class
            coreapi.Field(
                name="version",
                required=False,
                location='query',
                schema=coreschema.String(
                    title=force_str(_("api version")),
                    description=force_str(_("Response version '1.0' or '1.1'")),
                    pattern=r"\d\.\d",
                    default="1.0",
                )
            )
        ]


class TimespanView(generics.ListAPIView):
    serializer_class = ParkingDataV1Serializer
    pagination_class = TimestampV1Pagination
    versioning_class = TimespanVersioning
    queryset: QuerySet = ParkingData.objects.all()

    def get_queryset(self):
        version, versioning = self.determine_version(self.request)

        if version == "1.0":
            # TODO: original 1.0 response is hard to implement cleanly
            #   with the ListApiView. It should actually be another
            #   View class. But how to dispatch to different views
            #   by query parameter?
            return self.queryset.none()

        elif version == "1.1":
            return (
                # Note: the <city> url part is ignored
                self.queryset.filter(lot__lot_id=self.kwargs["lot_id"])
                # Note: original api response is not sorted
                .order_by("timestamp")
            )

        else:
            raise exceptions.ParseError(_(
                "Error 400: invalid API version, expecting one of '1.0', '1.1'"
            ))
