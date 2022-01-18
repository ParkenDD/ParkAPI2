import json
import os
import hashlib
import pickle
import datetime
from io import StringIO
from pathlib import Path
from typing import List, Dict, Type, Union, Generator, TextIO

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.http import HttpRequest
from rest_framework.request import Request

import requests

from api_v1.views import CityMapView, CityLotsView


CACHE_DIR: Path = settings.BASE_DIR / "cache" / "v1"


class Command(BaseCommand):
    help = 'Compare the current lot database with the v1 api.parkendd.de data'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        file = StringIO()
        compare_data(out=file)
        file.seek(0)
        print(file.read())


def compare_data(
        out: TextIO,
        caching: Union[bool, str] = True,
):
    response = request_parkendd("", caching=caching)
    pa1_city_map = response.json()["cities"]
    pa2_city_map = request_parkapi2_city_map()["cities"]

    print(f"\n{datetime.date.today()}\n\n", file=out)

    missing_in_pa2 = set(pa1_city_map) - set(pa2_city_map)
    if missing_in_pa2:
        print("\n# missing cities in ParkAPI2\n", file=out)
        for city in sorted(missing_in_pa2):
            print(f" - `{city}`", file=out)

    if 1:
        missing_in_dd = set(pa2_city_map) - set(pa1_city_map)
        # exclude the new scrapers ("bahn" pool is excluded by api v1 response)
        missing_in_dd -= {"Bielefeld", "Bochum", "Braunschweig", "Jena"}
        if missing_in_dd:
            print("\n### Cities that are in ParkAPI2 but not in ParkAPI1\n", file=out)
            for city in sorted(missing_in_dd):
                print(f" - `{city}`", file=out)

    print("\n## Comparison of city metadata:\n")

    for city in sorted(set(pa1_city_map) & set(pa2_city_map)):
        pa1_city_data = pa1_city_map[city]
        pa2_city_data = pa2_city_map[city]

        response = request_parkendd(city, caching=caching)
        pa1_city_lots = response.json()["lots"]
        pa2_city_lots = request_parkapi2_city_lots(city)["lots"]

        print(f"\n---\n\n## `{city}`\n", file=out)
        print(f"number of lots: {len(pa1_city_lots)} (pa1), {len(pa2_city_lots)} (pa2)\n", file=out)

        compare_city(pa1_city_data, pa2_city_data, out=out)

        missing_lots_pa1 = set(l["id"] for l in pa2_city_lots) - set(l["id"] for l in pa1_city_lots)
        if missing_lots_pa1:
            print("\n### lot_ids not in ParkAPI1:\n", file=out)
            print(", ".join(f"`{i}`" for i in sorted(missing_lots_pa1)), file=out)

        missing_lots_pa2 = set(l["id"] for l in pa1_city_lots) - set(l["id"] for l in pa2_city_lots)
        if missing_lots_pa2:
            print("\n### lot_ids not in ParkAPI2:\n", file=out)
            print(", ".join(f"`{i}`" for i in sorted(missing_lots_pa2)), file=out)


def compare_city(pa1: dict, pa2: dict, out: TextIO):
    differences = compare_dict(pa1, pa2, [])
    if differences:
        print_compare_table(differences, out=out)
        print(file=out)


def compare_dict(pa1: dict, pa2: dict, path: List[str]) -> dict:
    differences = dict()
    for key in sorted(set(pa1) | set(pa2)):
        path_key = ".".join(path + [key])
        if key not in pa1:
            differences[path_key] = ("*not present*", f"`{pa2[key]}`")
        elif key not in pa2:
            differences[path_key] = (f"`{pa1[key]}`", "*not present*")
        elif pa1[key] != pa2[key]:
            if isinstance(pa1[key], dict) or isinstance(pa2[key], dict):
                pa1_dict = pa1[key] or dict()
                pa2_dict = pa2[key] or dict()
                differences.update(compare_dict(pa1_dict, pa2_dict, path + [key]))
            else:
                differences[path_key] = (f"`{pa1[key]}`", f"`{pa2[key]}`")

    return differences


def print_compare_table(differences: dict, out: TextIO):
    widths = (
        max(len(i) for i in differences.keys())+2,
        max(len(i[0]) for i in differences.values()),
        max(len(i[1]) for i in differences.values()),
    )
    print(f"| {'path':{widths[0]}} | {'PA1':{widths[1]}} | {'PA2':{widths[2]}} |", file=out)
    print("|:{}|:{}|:{}|".format(
        "-" * (widths[0] + 1),
        "-" * (widths[1] + 1),
        "-" * (widths[2] + 1),
    ), file=out)
    for key, values in differences.items():
        key = f"`{key}`"
        print(f"| {key:{widths[0]}} | {values[0]:{widths[1]}} | {values[1]:{widths[2]}} |", file=out)
    print(file=out)


def request_parkendd(url_part: str, caching: Union[bool, str] = True) -> requests.Response:
    url = f"https://api.parkendd.de/{url_part}"
    cache_filename = CACHE_DIR / (hashlib.md5(url.encode("ascii")).hexdigest() + ".pkl")

    if caching in (True, "read"):
        if cache_filename.exists():
            return pickle.loads(cache_filename.read_bytes())

    response = requests.get(url)

    if caching in (True, "write"):
        os.makedirs(cache_filename.parent, exist_ok=True)
        cache_filename.write_bytes(pickle.dumps(response))

    return response


def request_parkapi2_city_map() -> dict:
    response = CityMapView().get(Request(HttpRequest()))
    return response.data


def request_parkapi2_city_lots(city_slug: str) -> dict:
    response = CityLotsView().get(Request(HttpRequest()), city_slug)
    return response.data
