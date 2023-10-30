from .base import *


class TestApiV1(TestBase):

    @classmethod
    def setUpTestData(cls):
        cls.store_location_fixtures()

        data_models = store_snapshot(cls.load_data("datteln-01.json"))
        location_model = Location.objects.get(city="Datteln")
        for data_model in data_models:
            data_model.lot.location = location_model
            data_model.lot.save()

        data_models = store_snapshot(cls.load_data("dresden-01.json"))
        location_model = Location.objects.get(city="Dresden")
        for data_model in data_models:
            data_model.lot.location = location_model
            data_model.lot.save()

    def test_100_root(self):
        response = self.client.get(reverse("api_v1:city-map")).data

        self.assertEqual("1.0", response["api_version"])
        self.assertEqual("https://github.com/ParkenDD/ParkAPI2", response["reference"])
        self.assertEqual(
            {
                "Datteln": {
                    "attribution": None,
                    "coords": {"lat": 51.6512192, "lng": 7.3393014},
                    "name": "Datteln",
                    "url": "https://www.apag.de",
                    # Return url as source url, if no explicit source url was defined
                    "source": "https://www.apag.de",
                    "active_support": False,
                },
                "Dresden": {
                    "attribution": {
                        "license": None,
                        "contributor": "Landeshauptstadt Dresden / tiefbauamt-verkehrstechnik@dresden.de",
                        "url": None
                    },
                    "coords": {"lat": 51.0493286, "lng": 13.7381437},
                    "name": "Dresden",
                    "url": "https://www.dresden.de/parken",
                    "source": "https://www.dresden.de/apps_ext/ParkplatzApp/",
                    "active_support": False,
                }
            },
            response["cities"],
        )

    def test_200_city(self):
        response = self.client.get(reverse("api_v1:city-lots", args=("Dresden", ))).data

        self.assertEqual(
            {
                'last_downloaded': datetime.datetime(2022, 3, 1, 17, 23, 52),
                'last_updated': datetime.datetime(2022, 3, 1, 17, 23, 36),
                'lots': [
                    {
                        'address': 'Altmarkt 1\n01067 Dresden\nEinfahrt von Wilsdruffer Straße\nEinfahrtshöhe max. 2,00 m\nKontakt: 03 51 / 481 02 74\nservicecenter@q-park.de',
                        'coords': {'lat': 51.0506700789, 'lng': 13.741789104},
                        'forecast': False,
                        'free': 154,
                        'id': 'dresdenaltmarkt',
                        'lot_type': 'Tiefgarage',
                        'name': 'Altmarkt',
                        'region': None,
                        'state': 'open',
                        'total': 400
                    },
                    {
                        'address': 'An der Frauenkirche 12a\n01067 Dresden\nEinfahrt von Schießgasse\nKontakt: 03 51 / 496 06 03\ntiefgarage-frauenkirche.dresden@gmx.de',
                        'coords': {'lat': 51.051415072, 'lng': 13.7441934672},
                        'forecast': False,
                        # Don't return free, if not available (to stay backward compatible with ParkAPIv1)
                        # 'free': None,
                        'id': 'dresdenanderfrauenkirche',
                        'lot_type': 'Tiefgarage',
                        'name': 'An der Frauenkirche',
                        'region': None,
                        'state': 'closed',
                        'total': 120
                    }
                ]
            },
            response,
        )
