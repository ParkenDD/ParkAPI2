from django.test import TestCase

from park_data.models import *


DATA1 = {
    "timestamp": "2000-01-01T00:00:00Z",
    "city": {
        "name": "Some City",
    },
    "state": {
        "name": "Some State"
    },
    "country": {
        "code": "DE",
        "name": "Germany",
    },
    "lots": [
        {
            "id": "some-city-1",
            "status": ParkingLotState.OPEN,
            "name": "Parkplatz 1",
            "address": "some street 42\nSome City",
            "num_free": 10,
            "num_total": 30,
        },
        {
            "id": "some-city-2",
            "status": ParkingLotState.CLOSED,
            "name": "Parkplatz 2",
            "address": "some other street 23\nSome City",
            "num_free": 0,
            "num_total": None,
        }
    ]
}


class TestData(TestCase):

    def test_store(self):
        lots = store_lot_data(DATA1)
        print(lots)

