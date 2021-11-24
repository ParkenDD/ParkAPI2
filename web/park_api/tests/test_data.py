from django.contrib.gis.geos import Point

from .base import *


class TestData(TestBase):

    def test_store(self):
        snapshot = self.load_data("snapshot01.json")

        data_models = store_snapshot(snapshot)

        self.assertEqual(207, data_models[0].capacity)
        self.assertEqual(197, data_models[0].num_free)
        self.assertEqual(197 / 207 * 100., data_models[0].percent_free)

        self.assertEqual((7.341648, 51.652461), data_models[0].lot.geo_point.tuple)
