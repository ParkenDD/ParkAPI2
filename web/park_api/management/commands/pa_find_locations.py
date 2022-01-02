import json
from typing import List, Dict, Type, Union, Generator

from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis import geos
from django.db import transaction
from django.conf import settings

from park_data.models import *
from locations.models import *
from locations.nominatim import NominatimApi


class Command(BaseCommand):
    help = 'Scrape all parking websites and store to database'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        find_locations(print_to_console=True)


def find_locations(
        caching: Union[bool, str] = True,
        print_to_console: bool = False,
):
    api = NominatimApi(verbose=print_to_console)
    open_lot_ids = list(
        ParkingLot.objects
        .filter(location=None)
        .exclude(geo_point=None)
        .values_list("lot_id", flat=True)
    )
    if print_to_console:
        if not open_lot_ids:
            print("All locations assigned")
        else:
            print(f"{len(open_lot_ids)} lots to find")

    for lot_id in open_lot_ids:
        lot_model = ParkingLot.objects.get(lot_id=lot_id)
        location_model = None

        # see if we have a Location that already contains
        #   the lot's geo-point
        existing_location_qset = Location.objects.filter(
            geo_polygon__contains=lot_model.geo_point
        )

        if existing_location_qset.exists():
            count = existing_location_qset.count()
            if count == 1:
                location_model = existing_location_qset[0]
                if print_to_console:
                    print(
                        f"'{lot_model}' is contained by existing location model polygon {location_model}"
                    )
            else:
                if print_to_console:
                    print(
                        f"'{lot_model}' is contained by {count} existing location models"
                        f", letting Nominatim decide..."
                    )

        if location_model is None:
            location_model = create_location_model(
                api=api,
                lot_model=lot_model,
                print_to_console=print_to_console,
                caching=caching,
            )

        lot_model.location = location_model
        lot_model.save()

        if print_to_console:
            print(f"assigned Location {location_model} to ParkingLot {lot_model}")


def create_location_model(
        api: NominatimApi,
        lot_model: ParkingLot,
        print_to_console: bool,
        caching: bool,
) -> Location:

    geo_point: geos.Point = lot_model.geo_point

    # --- request OSM data ---

    geojson = api.reverse(
        lon=geo_point.tuple[0],
        lat=geo_point.tuple[1],
        zoom=api.Zoom.city,
        format="geojson",
        extratags=1,
        addressdetails=1,
        namedetails=1,
        polygon_geojson=0,
        caching=caching,
    )
    # print(json.dumps(geojson, indent=2))

    addr = geojson["features"][0]["properties"]["address"]
    if "city" not in addr and "state" not in addr:
        # this fixes problem with "city-states" like Hamburg
        #   e.g. https://github.com/osm-search/Nominatim/issues/1759
        geojson = api.reverse(
            lon=geo_point.tuple[0],
            lat=geo_point.tuple[1],
            zoom=api.Zoom.state,
            format="geojson",
            extratags=1,
            addressdetails=1,
            namedetails=1,
            polygon_geojson=0,
            caching=caching,
        )

    feature = geojson["features"][0]
    props = feature["properties"]

    osm_id = "%s%s" % (
        props["osm_type"][0].upper(),
        props["osm_id"],
    )

    # -- already have the Location model with same OSM ID ? ---

    try:
        location_model = Location.objects.get(osm_id=osm_id)
        if print_to_console:
            print(f"'{osm_id}' already exists in database")

    # -- otherwise create new Location model

    except Location.DoesNotExist:

        # --- get the polygon data ---

        poly_geojson = api.lookup(
            osm_ids=[osm_id],
            format="geojson",
            polygon_geojson=1,
            caching=caching,
        )
        # print(json.dumps(poly_geojson, indent=2))

        poly_feature = poly_geojson["features"][0]

        poly_geom = geos.GEOSGeometry(json.dumps(poly_feature["geometry"]))
        polygon = None

        # some cities do not have a polygon attached and just
        #   return a point
        if poly_geom.geom_type == "Polygon":
            polygon = geos.MultiPolygon(poly_geom)
        elif poly_geom.geom_type == "MultiPolygon":
            polygon = poly_geom

        if print_to_console:
            print(f"creating Location '{osm_id}'")

        try:
            addr = props["address"]
            location_model = Location.objects.create(
                osm_id=osm_id,
                geo_point=geos.Point(*feature["geometry"]["coordinates"]),
                geo_polygon=polygon,
                osm_properties=props,
                city=(addr.get("town") or addr.get("city") or addr["state"])[:64],
                state=addr["state"][:64] if addr.get("state") else None,
                country=addr["country"][:64],
                country_code=addr["country_code"],
            )

        except KeyError:
            if print_to_console:
                print(f"\nCould not locate {lot_model} @ {lot_model.geo_point.tuple}\n")
                print(json.dumps(props, indent=2))
            raise

    return location_model

