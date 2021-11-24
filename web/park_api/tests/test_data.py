from .base import *


class TestData(TestBase):

    def test_store(self):
        snapshot = self.load_data("snapshot01.json")

        data_models = store_snapshot(snapshot)
        print(data_models)