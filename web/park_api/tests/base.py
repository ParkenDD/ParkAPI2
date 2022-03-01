from pathlib import Path
import json
import glob
import datetime
from typing import Tuple, List, Union

from django.test import TestCase
from django.urls import reverse
from django.contrib.gis.geos import Point
from django.core.serializers.json import DjangoJSONEncoder
from rest_framework.test import APIClient

from locations.models import Location
from park_data.models import *


class TestBase(TestCase):

    DATA_PATH = Path(__file__).resolve().parent / "data"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = APIClient()

    @classmethod
    def load_data(cls, filename: str) -> Union[dict, list]:
        return json.loads((cls.DATA_PATH / filename).read_text())

    @classmethod
    def store_location_fixtures(cls, filename: str = "locations.json"):
        data = cls.load_data(filename)
        for loc in data:
            loc["geo_point"] = Point(loc["geo_point"])
            Location.objects.create(**loc)

    @classmethod
    def dump(cls, data: Union[list, dict]):
        print(json.dumps(data, ensure_ascii=False, cls=DjangoJSONEncoder, indent=2))
