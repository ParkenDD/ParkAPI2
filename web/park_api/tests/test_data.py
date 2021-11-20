from .test_base import *


class TestData(TestBase):

    def test_store(self):
        locations, snapshots = self.load_snapshot_data("jena")

        # create locations
        lot_models = store_location_data(locations)

        # store snapshots
        for snapshot in snapshots:
            lot_models = store_lot_data(snapshot)

        # check the max_num_total counter
        self.assertEqual(
            28,
            ParkingLot.objects.get(lot_id="jena_busbahnhof").max_num_total,
        )

