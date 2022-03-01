from .base import *


class TestApiV2(TestBase):

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

    def test_100_pools(self):
        response = self.client.get("/api/v2/pools/").data

        pools = response["results"]
        pool_times = {
            pool["pool_id"]: pool["date_created"]
            for pool in pools
        }

        self.assertEqual(
            [
                {
                    "date_created": pool_times["apag"],
                    "date_updated": pool_times["apag"],
                    "pool_id": "apag",
                    "name": "Aachener Parkhaus GmbH",
                    "public_url": "https://www.apag.de",
                    "source_url": None,
                    "attribution_license": None,
                    "attribution_contributor": None,
                    "attribution_url": None,
                },
                {
                    "date_created": pool_times["dresden"],
                    "date_updated": pool_times["dresden"],
                    "pool_id": "dresden",
                    "name": "Dresden",
                    "public_url": "https://www.dresden.de/parken",
                    "source_url": "https://www.dresden.de/apps_ext/ParkplatzApp/",
                    "attribution_license": None,
                    "attribution_contributor": "Landeshauptstadt Dresden / tiefbauamt-verkehrstechnik@dresden.de",
                    "attribution_url": None,
                }
            ],
            response["results"],
        )

    def test_200_lots_geo_query(self):
        response = self.client.get("/api/v2/lots/?location=7.3,51&radius=100").data
        self.assertEqual(
            ["datteln-parkhaus-stadtgalerie", "datteln-parkdeck-stadtgalerie"],
            [lot["lot_id"] for lot in response["results"]]
        )

        response = self.client.get("/api/v2/lots/?location=13.8,51&radius=100").data
        self.assertEqual(
            ["dresdenanderfrauenkirche", "dresdenaltmarkt"],
            [lot["lot_id"] for lot in response["results"]]
        )
