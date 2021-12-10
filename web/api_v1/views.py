from copy import deepcopy
from typing import Dict

from rest_framework.views import APIView
from rest_framework.response import Response

from locations.models import Location
from park_data.models import ParkingLot, ParkingPool


class CityView(APIView):

    def get(self, request):

        return Response({
            "api_version": "1.0",
            "server_version": "0.3.666",
            "reference": "https://github.com/offenesdresden/ParkAPI",
            "cities": self.city_mapping(),
        })

    @classmethod
    def city_mapping(cls) -> Dict:
        pool_map = {
            pool.pop("pk"): pool
            for pool in ParkingPool.objects.all().values(
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

        lot_qset = ParkingLot.objects.exclude(location=None)
        city_map = dict()
        for loc_pk, pool_pk in lot_qset.values_list("location__pk", "pool__pk"):
            loc = location_map[loc_pk]
            if loc["city"] not in city_map:

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
                    "coords": {"lng": lng, "lat": lat},
                    "name": loc["city"],
                    "url": city.pop("public_url"),
                    "source": city.pop("source_url"),
                    # TODO: no db-field yet
                    "active_support": False,
                })

                city_map[loc["city"]] = city

        city_map = {
            city: city_map[city]
            for city in sorted(city_map)
        }
        return city_map
