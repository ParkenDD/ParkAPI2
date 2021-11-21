from pathlib import Path
import json
import glob
from typing import Tuple, List, Union

from django.test import TestCase

from park_data.models import *


class TestBase(TestCase):

    DATA_PATH = Path(__file__).resolve().parent / "data"

    def load_data(self, filename: str) -> Union[dict, list]:
        return json.loads((self.DATA_PATH / filename).read_text())

    def load_snapshot_data(self, path: str) -> Tuple[dict, List[dict]]:
        locations = self.load_data(str(Path(path) / f"locations.json"))
        snapshots = self.load_data(str(Path(path) / f"snapshots.json"))
        return locations, snapshots
