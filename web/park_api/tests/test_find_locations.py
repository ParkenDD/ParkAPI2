import unittest

from django.test import TestCase
from django.contrib.gis import geos

from decouple import config

from park_data.models import *
from locations.models import *
from locations.nominatim import NominatimApi
from park_api.management.commands.pa_find_locations import create_location_model


@unittest.skipIf(
    not config("PA_TEST_EXTERNAL_API", False),
    "test_find_locations.py is skipped unless PA_TEST_EXTERNAL_API is defined in"
    " environment or `.env` file"
)
class TestFindLocations(TestCase):

    def setUp(self):
        self.api = NominatimApi(verbose=True)

    def create_lot_model(self, name: str, longitude: float, latitude: float):
        pool_model = ParkingPool.objects.create(
            pool_id=f"pool-{name}",
            name=f"Pool {name}",

        )
        lot_model = ParkingLot.objects.create(
            pool=pool_model,
            lot_id=name,
            name=name,
            geo_point=geos.Point(longitude, latitude),
            has_live_capacity=False,
        )
        return lot_model

    def get_location_model(self, lot_model: ParkingLot):
        return create_location_model(
            api=self.api,
            lot_model=lot_model,
            print_to_console=True,
            caching=True,
        )

    def test_locations_hamburg(self):
        # Central Hamburg
        central_lot_1 = self.create_lot_model("central-1", 9.991765368130983, 53.55266863496544)
        central_lot_2 = self.create_lot_model("central-2", 10.001305675289679, 53.54248537737457)
        # Ellerau - which is a **village** outside of Hamburg
        outside_lot_1 = self.create_lot_model("outside-1", 9.94323429789424, 53.755514531002454)
        # Dahlenburg
        outside_lot_2 = self.create_lot_model("outside-2", 10.708917159521013, 53.16969723701287)

        location = self.get_location_model(central_lot_1)
        self.assertEqual("Hamburg", location.city)
        self.assertEqual("Hamburg", location.state)

        location = self.get_location_model(central_lot_2)
        self.assertEqual("Hamburg", location.city)
        self.assertEqual("Hamburg", location.state)

        location = self.get_location_model(outside_lot_1)
        self.assertEqual("Ellerau", location.city)
        self.assertEqual("Schleswig-Holstein", location.state)

        location = self.get_location_model(outside_lot_2)
        self.assertEqual("Dahlenburg", location.city)
        self.assertEqual("Niedersachsen", location.state)
