import datetime
import posix
from copy import deepcopy
from typing import Dict

from rest_framework import views, renderers, generics, parsers
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.schemas.openapi import AutoSchema
from locations.models import Location
from park_data.models import ParkingLot, ParkingPool, ParkingData, ParkingLotState


# legacy name -> nominatim name
CITY_NAME_LEGACY_TO_NOMINATIM = {
    "Buchholz": "Buchholz in der Nordheide",  # This one's actually in the Hamburg pool
    "Frankfurt": "Frankfurt am Main",
    "Freiburg": "Freiburg im Breisgau",
    "Koeln": "Köln",
    "Limburg": "Limburg an der Lahn",
    "Luebeck": "Lübeck",
    "Muenster": "Münster",
    "Nuernberg": "Nürnberg",
    "Zuerich": "Zürich",

    # from DB-API
    "Halle": "Halle (Saale)",
    "Muenchen": "München"
}

CITY_NAME_NOMINATIM_TO_LEGACY = {
    value: key
    for key, value in CITY_NAME_LEGACY_TO_NOMINATIM.items()
}


LOT_TYPE_MAPPING = {
    "lot": "Parkplatz",
    "underground": "Tiefgarage",
    "garage": "Parkhaus",
    "level": "Parkebene",
    "bus": "Busparkplatz",
    "unknown": "unbekannt",
}


class StatusView(views.APIView):

    def get(self, request):
        return Response({
            "status": "online",
            "server_time": datetime.datetime.utcnow().replace(microsecond=0),
            "load": posix.getloadavg()
        })


class CoffeeView(views.APIView):
    renderer_classes = (renderers.StaticHTMLRenderer, renderers.JSONRenderer)

    def get(self, request: Request):
        return Response("""
        <h1>I'm a teapot</h1>
        <p>This server is a teapot, not a coffee machine.</p><br>
        <img src="http://i.imgur.com/xVpIC9N.gif"
            alt="British porn"
            title="British porn"/>
        """, status=418)


class CityMapView(views.APIView):

    def get(self, request: Request):

        return Response({
            "api_version": "1.0",
            "server_version": "0.3.666",
            "reference": "https://github.com/offenesdresden/ParkAPI",
            "cities": self.city_mapping(),
        })

    @classmethod
    def city_mapping(cls) -> Dict:
        """
        Return legacy 'meta' data per city.

        Uses 3 db queries to build the map of city name to city meta data.
        The first lot location that matches the city name is merged
        with it's pool data to create the v1 city data.

        Note: This currently excludes the DeutscheBahn pool because
            1. it can mess up another city's attribution
            2. adds a lot of cities with just one parking lot
        """
        pool_map = {
            pool.pop("pk"): pool
            for pool in ParkingPool.objects.exclude(pool_id="bahn").values(
                "pk", "public_url", "source_url",
                "attribution_license", "attribution_contributor", "attribution_url"
            )
        }
        location_map = {
            loc.pop("pk"): loc
            for loc in Location.objects.all().values(
                "pk", "geo_point", "city", "osm_properties",
            )
        }

        lot_qset = (
            ParkingLot.objects.exclude(location=None)
            # order the set for consistent city->pool matching
            .order_by("lot_id")
        )
        city_map = dict()
        for loc_pk, pool_pk in lot_qset.values_list("location__pk", "pool__pk"):
            loc = location_map[loc_pk]
            city_name = CITY_NAME_NOMINATIM_TO_LEGACY.get(loc["city"], loc["city"])
            if city_name not in city_map:

                city = deepcopy(pool_map[pool_pk])
                city["attribution"] = {
                    "license": city.pop("attribution_license"),
                    "contributor": city.pop("attribution_contributor"),
                    "url": city.pop("attribution_url")
                }
                if not any(city["attribution"].values()):
                    city["attribution"] = None

                lng, lat = loc["geo_point"].tuple
                city.update({
                    "coords": {"lat": lat, "lng": lng},
                    "name": loc["city"],
                    "url": city.pop("public_url"),
                    "source": city.pop("source_url"),
                    # TODO: no db-field yet
                    "active_support": False,
                })

                city_map[city_name] = city

        city_map = {
            city: city_map[city]
            for city in sorted(city_map)
        }
        return city_map


class CityLotsView(views.APIView):

    def get(self, request: Request, city: str):

        location_qset = Location.objects.filter(city__iexact=CITY_NAME_LEGACY_TO_NOMINATIM.get(city, city))
        if not location_qset.exists():
            return Response({
                "detail": f"Error 404: Sorry, '{city}' isn't supported at the current time."
            }, status=404)

        # currently there's only city-level locations
        location_model = location_qset[0]

        lot_qset = ParkingLot.objects.filter(location=location_model).order_by("lot_id")

        api_lot_list = []
        last_downloaded = None
        last_updated = None

        for lot in lot_qset:
            if lot.geo_point:
                lng, lat = lot.geo_point.tuple
                coords = {"lat": lat, "lng": lng}
            else:
                coords = None

            api_lot = {
                "address": lot.address,
                "coords": coords,
                "forecast": False,  # TODO
                "free": None,
                "id": lot.lot_id,
                "lot_type": LOT_TYPE_MAPPING.get(lot.type, "unbekannt"),
                "name": lot.name,
                "region": None,  # TODO
                "state": None,
                "total": lot.max_capacity,
            }
            if lot.latest_data:
                api_lot.update({
                    "free": lot.latest_data.num_free,
                    "state": lot.latest_data.status,
                })
                if lot.latest_data.capacity is not None:
                    api_lot["total"] = lot.latest_data.capacity

                if last_downloaded is None or lot.latest_data.timestamp > last_downloaded:
                    last_downloaded = lot.latest_data.timestamp
                if last_updated is None or (
                        lot.latest_data.lot_timestamp and lot.latest_data.lot_timestamp > last_updated
                ):
                    last_updated = lot.latest_data.lot_timestamp

            api_lot_list.append(api_lot)

        return Response({
            "last_downloaded": last_downloaded,
            "last_updated": last_updated,
            "lots": api_lot_list,
        })

