from pathlib import Path
import json
import glob
from typing import Tuple, List

from django.test import TestCase

from park_data.models import *


DATA_PATH = Path(__file__).resolve().parent / "data"


class TestData(TestCase):

    def load_data(self, key: str) -> Tuple[dict, List[dict]]:
        locations = json.loads((DATA_PATH / key / f"locations.json").read_text())
        snapshots = []
        for filename in sorted(glob.glob(str(DATA_PATH / key / "lots-*.json"))):
            snapshots.append(json.loads(Path(filename).read_text()))
        return locations, snapshots

    def test_store(self):
        locations, snapshots = self.load_data("jena")

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
