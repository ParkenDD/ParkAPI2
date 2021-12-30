import os
import re
import time
import hashlib
import json
import datetime
from pathlib import Path
import tempfile
import pickle
import pytz
import argparse
import glob
import importlib
import sys
import inspect
from typing import Union, Optional, Tuple, List, Type, Dict

import requests
from bs4 import BeautifulSoup

from .structs import PoolInfo, LotInfo, LotData
from .dt import to_utc_datetime
from ._log import log
from .strings import name_to_legacy_id, guess_lot_type


VERSION = (0, 0, 1)

MODULE_DIR: Path = Path(__file__).resolve().parent


class ScraperBase:

    # Directory where web requests are cached
    CACHE_DIR = Path(tempfile.gettempdir()) / "parkapi-scraper"

    # Maximum requests allowed per second
    REQUESTS_PER_SECOND: float = 2.
    # The user agent that is used in web requests
    USER_AGENT = "github.com/defgsus/ParkAPI2"
    # Extra headers that should be added to all requests
    HEADERS = {}

    # A PoolInfo object must be specified for each derived scraper
    POOL: PoolInfo = None

    # ---- internals ----

    __last_request_time = 0

    def __init_subclass__(cls, **kwargs):
        if not isinstance(cls.POOL, PoolInfo):
            raise ValueError(f"Must specify {cls.__name__}.POOL = PoolInfo(...)")

    def __init__(
            self,
            caching: Union[bool, str] = False,
    ):
        """
        Initializes a scraper class and a requests.Session

        :param caching: bool|str
            Enable file-caching, can be True, False, "read" or "write"

            For developing a scraper it's good practice to set
            `caching=True` to avoid repeated similar requests
            against the website.
        """
        self.caching = caching
        self.session = requests.Session()
        self.session.headers = {
            "User-Agent": self.USER_AGENT,
        }

    # ---------- methods that need implementation -------------

    def get_lot_data(self) -> List[LotData]:
        raise NotImplementedError

    # ------------------- LotInfo data ------------------------

    def get_lot_infos(self) -> List[LotInfo]:
        raise NotImplementedError

    def get_lot_infos_from_geojson(self) -> Optional[List[LotInfo]]:
        filename = Path(inspect.getfile(self.__class__)[:-3] + ".geojson")
        if filename.exists():
            geojson = json.loads(filename.read_text())
            infos = []
            for feature in geojson["features"]:
                lot_info = feature["properties"].copy()

                if feature.get("geometry"):
                    if feature["geometry"]["type"] != "Point":
                        raise ValueError(
                            f"""geometry type '{feature["geometry"]["type"]}' for lot '{lot_info["id"]}' not supported"""
                        )
                    lot_info["latitude"] = feature["geometry"]["coordinates"][1]
                    lot_info["longitude"] = feature["geometry"]["coordinates"][0]

                infos.append(LotInfo.from_dict(lot_info))
            return infos

    def get_lot_info_map(self, required: bool = True) -> Dict[str, LotInfo]:
        lot_infos = self.get_lot_infos_from_geojson()
        if not lot_infos:
            try:
                lot_infos = self.get_lot_infos()
            except NotImplementedError:
                if required:
                    raise NotImplementedError(
                        f"You need to either implement {self.__class__.__name__}.get_lot_infos()"
                        f" or create a {Path(inspect.getfile(self.__class__)).name[:-3]}.geojson file"
                    )
                else:
                    return dict()

        lot_ids = set()
        for info in lot_infos:
            if info.id in lot_ids:
                raise ValueError(
                    f"Duplicate LotInfo id '{info.id}' in pool '{self.POOL.id}'"
                )
            lot_ids.add(info.id)

        return {
            info.id: info
            for info in lot_infos
        }

    # ------------------ scraping helpers ---------------------

    def request(
            self,
            url: str,
            method: str = "GET",
            expected_status: Optional[int] = None,
            caching: Optional[Union[bool, str]] = None,
            **kwargs,
    ) -> requests.Response:
        """
        Request any url from the web.

        Will throttle all requests to the REQUESTS_PER_SECOND value.

        :param url: str, Fully qualified web url
        :param method: str, The HTTP method
        :param expected_status: int|None, Raises error when returned status differs.
        :param caching: bool|str|None, Override the file-caching setting, can be True, False, "read" or "write"
        :param kwargs: any arguments to requests.request() except "method" and "url"

        :return: requests.Response instance
        """
        # -- put headers together --

        headers = self.HEADERS.copy()
        if kwargs.get("headers"):
            headers.update(kwargs["headers"])
        if headers:
            kwargs["headers"] = headers

        # -- check file cache --

        cache_name = None
        caching = self.caching if caching is None else caching
        if caching:
            cache_name = hashlib.md5(f"{method} {url} {kwargs}".encode("utf-8")).hexdigest()
            cache_name = self.CACHE_DIR / self.POOL.id / f"{cache_name}.pkl"

        if caching in (True, "read"):
            if cache_name.exists():
                log(f"loading cache {cache_name}")
                return pickle.loads(cache_name.read_bytes())

        # -- throttle requests --

        passed_time = time.time() - self.__last_request_time
        if passed_time < 1. / self.REQUESTS_PER_SECOND:
            time.sleep(1. / self.REQUESTS_PER_SECOND - passed_time)
        self.__last_request_time = time.time()

        display_kwargs = kwargs.copy()
        display_kwargs.pop("headers", None)
        log(f"requesting {method} {url} {display_kwargs or ''}")

        response = self.session.request(
            method=method,
            url=url,
            **kwargs,
        )

        # -- validate status --

        if expected_status is not None:
            if response.status_code != expected_status:
                raise IOError(
                    f"Unexpected status {response.status_code} for request {method} {url} {kwargs}"
                    f"\n\nResponse: {response.content}"
                )

        # -- store cache --

        if caching in (True, "write"):
            log(f"writing cache to {cache_name}")
            os.makedirs(str(self.CACHE_DIR / self.POOL.id), exist_ok=True)
            cache_name.write_bytes(pickle.dumps(response))

        return response

    def request_json(
            self,
            url: str,
            method: str = "GET",
            expected_status: int = 200,
            caching: Optional[Union[bool, str]] = None,
            **kwargs,
    ) -> Union[dict, list]:
        response = self.request(
            url=url, method=method,
            expected_status=expected_status,
            caching=caching,
            headers={"Accept": "application/json"},
            **kwargs,
        )
        try:
            return response.json()
        except:
            print("\n", file=sys.stderr)
            print("RESPONSE CONTENT:", file=sys.stderr)
            print(response.content, file=sys.stderr)
            raise

    def request_soup(
            self,
            url: str,
            method: str = "GET",
            expected_status: Optional[int] = None,
            caching: Optional[Union[bool, str]] = None,
            parser: str = "html.parser",
            **kwargs,
    ) -> BeautifulSoup:
        response = self.request(
            url=url, method=method,
            expected_status=expected_status,
            caching=caching,
            **kwargs,
        )
        return BeautifulSoup(response.text, features=parser)

    @classmethod
    def now(cls) -> datetime.datetime:
        """
        Return current UTC datetime
        """
        return datetime.datetime.utcnow().replace(microsecond=0)

    @classmethod
    def to_utc_datetime(
            cls,
            date_string: str,
            date_format: Optional[str] = None,
            timezone: Optional[str] = None
    ) -> datetime.datetime:
        """
        Convert a date string into a UTC datetime.

        Will always raise ValueError if parsing fails.

        :param date_string: str, The date string
        :param date_format: str|None
            Optional format for parsing the date string.
            defaults to Scraper.POOL.timezone.

        :param timezone: str|None
            The timezone of the parsed date,
            defaults to Scraper.POOL.timezone

        :return: datetime, in UTC but without tzinfo
        """
        return to_utc_datetime(
            date_string,
            date_format=date_format,
            timezone=cls.POOL.timezone if timezone is None else timezone,
        )

    def get_v1_lot_infos_from_geojson(self, name: str, defaults: Optional[dict] = None) -> List[LotInfo]:
        """
        Transitional helper to download and parse the original ParkAPI geojson file.

        :param name: str, without extension, something like "Dresden"
        :param defaults: dict, default values for each LotInfo
        :return: list of LotInfo instances
        """
        url = f"https://github.com/offenesdresden/ParkAPI/raw/master/park_api/cities/{name}.geojson"
        response = self.request(url)
        assert (
            response.status_code == 200,
            f"Did not find original geojson '{url}', status {response.status_code}"
        )

        data = response.json()
        lots = []

        for feature in data["features"]:
            props = feature["properties"]
            if props["type"] == "city":
                continue

            lot_type = defaults.get("type")
            if not lot_type:
                lot_type = guess_lot_type(props["type"])

            lots.append(
                LotInfo(
                    **defaults,
                    id=name_to_legacy_id(self.POOL.id, props["name"]),
                    name=props["name"],
                    type=lot_type,
                    capacity=props["total"],
                    longitude=feature["geometry"]["coordinates"][0],
                    latitude=feature["geometry"]["coordinates"][1],
                    address=props.get("address"),
                )
            )

        return lots
