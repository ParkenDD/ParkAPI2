import json
from pathlib import Path
from typing import List, Dict, Type, Union, Generator

from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis import geos
from django.db import transaction
from django.conf import settings

from park_data.models import *
from locations.models import *
from locations.nominatim import NominatimApi


CACHE_DIR: Path = settings.BASE_DIR / "cache" / "v1"


class Command(BaseCommand):
    help = 'Compare the current lot database with the v1 api.parkendd.de data'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        compare_data()


def compare_data(
        caching: Union[bool, str] = True,
):
    pass
    #if caching == "write"