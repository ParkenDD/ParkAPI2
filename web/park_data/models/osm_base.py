import json
from typing import Optional

from django.utils.translation import gettext_lazy as _
from django.contrib.gis.db import models
from django.contrib.gis import geos

from ..nominatim import NominatimApi


class OSMBase(models.Model):

    class Meta:
        abstract = True

    osm_id = models.CharField(
        verbose_name=_("OpenStreetMap ID"),
        help_text=_("The ID must be prefixed with N, W or R (for Node, Way or Relation)"),
        max_length=32,
        unique=True,
        db_index=True,
    )

    created_at = models.DateTimeField(
        verbose_name=_("Date of creation"),
        auto_now_add=True, editable=False,
        db_index=True,
    )

    name = models.CharField(
        verbose_name=_("Name"),
        max_length=64,
        null=True, blank=True,
        db_index=True,
    )

    geo_point = models.PointField(
        verbose_name=_("Geographic center"),
        null=True, blank=True,
        db_index=True,
    )

    geo_polygon = models.MultiPolygonField(
        verbose_name=_("Geographic outline"),
        null=True, blank=True,
        db_index=True,
    )

    def __str__(self):
        s = self.osm_id
        if self.name:
            s = f"{s}/{self.name}"
        return s
        # return f"{self.__class__.__name__}('{self.name}', '{self.osm_id}')"

    def update_from_nominatim_geojson(self, data: dict):
        """
        Update the model fields from geojson data retrieved from nominatim api

        :param data: a single nominatim geojson entry
        """
        osm_id = None

        for i, feature in enumerate(data["features"]):
            props = feature["properties"]
            if "osm_type" not in props:
                raise ValueError(f"Missing attribute 'features.{i}.properties.osm_type'")
            if "osm_id" not in props:
                raise ValueError(f"Missing attribute 'features.{i}.properties.osm_id'")

            osm_id = props["osm_type"][0].upper() + str(props["osm_id"])
            if self.osm_id == osm_id:

                if not self.name:
                    self.name = props["display_name"][:32]

                if "geometry" in feature:
                    geom = geos.GEOSGeometry(json.dumps(feature["geometry"]))

                    if geom.geom_type == "Point":
                        self.geo_point = geom
                    elif geom.geom_type == "MultiPolygon":
                        self.geo_polygon = geom
                    elif geom.geom_type == "Polygon":
                        self.geo_polygon = geos.MultiPolygon(geom)

                return

        if not osm_id:
            raise ValueError(f"No features in geojson")

        raise ValueError(f"osm_id '{osm_id}' does not fit model's '{self.osm_id}")

    def update_from_nominatim_api(self, api: Optional[NominatimApi] = None):
        """
        Update the model fields from geojson data from nominatim api.

        The API is queried unless there is a cache file present
        """
        if api is None:
            api = NominatimApi()

        if not self.geo_point:
            data = api.lookup(
                osm_ids=[self.osm_id],
                extratags=1,
                addressdetails=1,
                polygon_geojson=0,
            )
            self.update_from_nominatim_geojson(data)

        if not self.geo_polygon:
            data = api.lookup(
                osm_ids=[self.osm_id],
                extratags=0,
                addressdetails=0,
                polygon_geojson=1,
            )
            self.update_from_nominatim_geojson(data)

