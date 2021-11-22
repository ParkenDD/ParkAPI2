import json
from typing import Optional

from django.utils.translation import gettext_lazy as _
from django.contrib.gis.db import models
from django.contrib.gis import geos

from park_data.nominatim import NominatimApi


class OSMLocation(models.Model):

    class Meta:
        verbose_name = _("OSM Location")
        verbose_name_plural = _("OSM Locations")

    date_created = models.DateTimeField(
        verbose_name=_("Date of creation"),
        auto_now_add=True, editable=False,
        db_index=True,
    )

    date_updated = models.DateTimeField(
        verbose_name=_("Date of update"),
        auto_now=True, editable=False,
        db_index=True,
    )

    osm_id = models.CharField(
        verbose_name=_("OpenStreetMap ID"),
        help_text=_("The ID must be prefixed with N, W or R (for Node, Way or Relation)"),
        max_length=32,
        unique=True,
        db_index=True,
    )

    osm_parent = models.ForeignKey(
        verbose_name=_("Administrative parent"),
        to="OSMLocation",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        db_index=True,
    )

    osm_place_rank = models.IntegerField(
        verbose_name=_("Place rank"),
        help_text=_("The higher, the smaller"),
        null=True, blank=True,
        db_index=True,
    )

    osm_feature_type = models.CharField(
        verbose_name=_("Type of object"),
        help_text=_("This is not the 'osm_type', it's simply the 'type'"),
        max_length=32,
        null=True, blank=True,
        db_index=True,
    )

    osm_linked_place = models.CharField(
        verbose_name=_("Type of place"),
        help_text=_("Comes from OSM 'feature.extratags.linked_place'"),
        max_length=32,
        null=True, blank=True,
        db_index=True,
    )

    osm_properties = models.JSONField(
        verbose_name=_("Properties from OSM"),
        null=True, blank=True,
    )

    #country_code = models.CharField(
    #    verbose_name=_("ISO 3166 country code"),
    #    max_length=2,
    #)

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

    @classmethod
    def create_from_nominatim_geojson_feature(cls, feature: dict, do_save: bool = True) -> "OSMLocation":
        props = feature["properties"]
        if "osm_type" not in props:
            raise ValueError(f"Missing attribute 'properties.osm_type'")
        if "osm_id" not in props:
            raise ValueError(f"Missing attribute 'properties.osm_id'")
        osm_id = props["osm_type"][0].upper() + str(props["osm_id"])

        model = cls(
            osm_id=osm_id
        )
        model.update_from_nominatim_geojson_feature(feature)
        if do_save:
            model.save()
        return model

    def update_from_nominatim_geojson_feature(self, feature: dict):
        """
        Update the model fields from a geojson feature.

        Can be overridden by subclasses which should call the super() method
        """
        props = feature["properties"]

        self.osm_properties = props

        if not self.name:
            name = props["display_name"]
            # don't need the whole name tail for suburbs, cities and above
            if props["type"] == "administrative":
                self.name = name.split(",")[0].strip()[:64]
            else:
                self.name = ", ".join(s.strip() for s in name.split(",")[:4])[:64]

        if "place_rank" in props:
            self.osm_place_rank = props["place_rank"]

        if props.get("type"):
            self.osm_feature_type = props["type"][:32]

        if props.get("extratags") and props["extratags"].get("linked_place"):
            self.osm_linked_place = props["extratags"]["linked_place"]

        if "geometry" in feature:
            geom = geos.GEOSGeometry(json.dumps(feature["geometry"]))

            if geom.geom_type == "Point":
                self.geo_point = geom
            elif geom.geom_type == "MultiPolygon":
                self.geo_polygon = geom
            elif geom.geom_type == "Polygon":
                self.geo_polygon = geos.MultiPolygon(geom)

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

                self.update_from_nominatim_geojson_feature(feature)

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

        if not self.geo_point or not self.name:
            data = api.lookup(
                osm_ids=[self.osm_id],
                extratags=1,
                addressdetails=1,
                namedetails=1,
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

