import json
from typing import List, Dict, Type, Union, Generator, Optional

from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis import geos
from django.contrib.gis.db.models import functions as F
from django.db import transaction
from django.conf import settings

from park_data.models import *
from locations.models import *
from locations.nominatim import NominatimApi


class Command(BaseCommand):
    help = 'Use OSM Nominatim for reverse search and create and attach' \
           ' a Location to each ParkingLot'

    def add_arguments(self, parser):
        parser.add_argument(
            "-p", "--pools", nargs="+", type=str,
            help="Filter for one or more pool IDs"
        )

    def handle(self, *args, pools, **options):
        find_locations(pools=pools, print_to_console=True)


def find_locations(
        pools: Optional[List[str]],
        caching: Union[bool, str] = True,
        print_to_console: bool = False,
):
    api = NominatimApi(verbose=print_to_console)

    open_lot_qset = (
        ParkingLot.objects
        .filter(location=None)
        .exclude(geo_point=None)
    )
    if pools:
        open_lot_qset = open_lot_qset.filter(pool__pool_id__in=pools)
    open_lot_ids = list(
        open_lot_qset
        .values_list("lot_id", flat=True)
        .order_by("lot_id", "pool__pool_id")
    )

    if print_to_console:
        if not open_lot_ids:
            print("All locations assigned")
        else:
            print(f"{len(open_lot_ids)} lots to find")

    last_pool_id = None
    for lot_id in open_lot_ids:
        lot_model = ParkingLot.objects.get(lot_id=lot_id)
        location_model = None

        # keep track of changing pool
        new_pool = False
        if lot_model.pool.pool_id != last_pool_id:
            new_pool = True
        last_pool_id = lot_model.pool.pool_id

        if new_pool:
            # when starting to find locations for a new pool
            #   rather ask nominatim first and do not
            #   lookup existing polygons
            existing_location_qset = Location.objects.none()
        else:
            # see if we have a Location that already contains
            #   the lot's geo-point
            existing_location_qset = (
                Location.objects.filter(geo_polygon__contains=lot_model.geo_point)
                # this could be used to pick the smallest area
                #   currently nominatim is queried when more than one
                #   location exists
                # .annotate(area=F.Area('geo_polygon'))
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

    geojson = nominatim_reverse_search(api=api, lot_model=lot_model, caching=caching)

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
                city=(
                    addr.get("suburb") or addr.get("village") or addr.get("town")
                    or addr.get("city") or addr.get("county") or addr["state"]
                )[:64],
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


def nominatim_reverse_search(api: NominatimApi, lot_model: ParkingLot, caching: bool) -> dict:
    geo_point: geos.Point = lot_model.geo_point

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
    if "village" in addr or "town" in addr or "city" in addr or "state" in addr:
        return geojson

    # If we do not get "city" nor "state" that means
    #   that either it's a "city-state" like Hamburg
    #   (e.g. https://github.com/osm-search/Nominatim/issues/1759)
    #   or it's maybe a town/village/suburb

    # try village first
    geojson = api.reverse(
        lon=geo_point.tuple[0],
        lat=geo_point.tuple[1],
        zoom=api.Zoom.village,
        format="geojson",
        extratags=1,
        addressdetails=1,
        namedetails=1,
        polygon_geojson=0,
        caching=caching,
    )

    addr = geojson["features"][0]["properties"]["address"]
    if "village" in addr or "town" in addr or "city" in addr or "state" in addr:
        return geojson

    # if no village, it's most likely a state
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
    addr = geojson["features"][0]["properties"]["address"]

    if not ("village" in addr or "town" in addr or "city" in addr or "state" in addr):
        # finally try suburb
        geojson = api.reverse(
            lon=geo_point.tuple[0],
            lat=geo_point.tuple[1],
            zoom=api.Zoom.suburb,
            format="geojson",
            extratags=1,
            addressdetails=1,
            namedetails=1,
            polygon_geojson=0,
            caching=caching,
        )

    addr = geojson["features"][0]["properties"]["address"]
    if not ("suburb" in addr or "village" in addr or "town" in addr or "city" in addr or "state" in addr):
        raise ValueError(
            f"Nominatim reverse search for lot {lot_model} with coords {geo_point.tuple}"
            f" did not yield a 'suburb', 'town', 'city' or 'state', got: {addr}"
        )

    return geojson
