import json

from django.utils.translation import gettext_lazy as _
from django.contrib.gis.db import models
from django.contrib.gis.geos import GEOSGeometry


class OSMBase(models.Model):

    class Meta:
        abstract = True

    osm_id = models.CharField(
        verbose_name=_("OpenStreetMap ID"),
        help_text=_("The ID must be prefixed with N, W or R (for Node, Way or Relation)"),
        primary_key=True,
        max_length=32,
    )

    created_at = models.DateTimeField(
        verbose_name=_("Date of creation"),
        auto_now_add=True,
        db_index=True,
        editable=False,
    )

    name = models.CharField(
        verbose_name=_("Name"),
        max_length=64,
        null=True,
        db_index=True,
    )

    geo_point = models.PointField(
        verbose_name=_("Geographic center"),
        null=True,
        db_index=True,
    )

    geo_polygon = models.MultiPolygonField(
        verbose_name=_("Geographic outline"),
        null=True,
        db_index=True,
    )

    def update_from_nominatim_geojson(self, data: dict):
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
                    geom = GEOSGeometry(json.dumps(feature["geometry"]))

                    if geom.geom_type == "Point":
                        self.geo_point = geom
                    elif geom.geom_type in ("Polygon", "MultiPolygon"):
                        self.geo_polygon = geom

                return

        if not osm_id:
            raise ValueError(f"No features in geojson")

        raise ValueError(f"osm_id '{osm_id}' does not fit model's '{self.osm_id}")
