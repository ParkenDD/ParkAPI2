import json
from typing import List, Dict, Type, Union, Generator

from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis.geos import Point
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

        geojson = api.reverse(
            lon=lot_model.geo_point.tuple[0],
            lat=lot_model.geo_point.tuple[1],
            zoom=api.Zoom.city,
            format="geojson",
            extratags=1,
            addressdetails=1,
            namedetails=1,
            caching=caching,
        )
        # print(json.dumps(geojson, indent=2))

        feature = geojson["features"][0]
        props = feature["properties"]

        osm_id = "%s%s" % (
            props["osm_type"][0].upper(),
            props["osm_id"],
        )

        try:
            location_model = Location.objects.get(osm_id=osm_id)
            if print_to_console:
                print(f"'{osm_id}' already exists in database")

        except Location.DoesNotExist:
            if print_to_console:
                print(f"creating Location '{osm_id}'")

            try:
                addr = props["address"]
                location_model = Location.objects.create(
                    osm_id=osm_id,
                    geo_point=Point(*feature["geometry"]["coordinates"]),
                    osm_properties=props,
                    city=(addr.get("town") or addr.get("city") or addr["state"])[:64],
                    state=addr["state"][:64] if addr.get("state") else None,
                    country=addr["country"][:64],
                    country_code=addr["country_code"],
                )

            except KeyError:
                print(json.dumps(props, indent=2))
                raise

        lot_model.location = location_model
        lot_model.save()

        if print_to_console:
            print(f"assigned Location {location_model} to ParkingLot {lot_model}")
