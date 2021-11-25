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
import unicodedata
from typing import Union, Optional, Tuple, List, Type, Dict

import requests
from bs4 import BeautifulSoup

from .structs import PoolInfo, LotInfo, LotData


VERSION = (0, 0, 1)

MODULE_DIR: Path = Path(__file__).resolve().parent


def log(*args, **kwargs):
    print(datetime.datetime.now(), *args, **kwargs, file=sys.stderr)


class ScraperBase:

    CACHE_DIR = Path(tempfile.gettempdir()) / "parkapi-scraper"
    REQUESTS_PER_SECOND = 2.
    USER_AGENT = "github.com/defgsus/ParkAPI2"

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
                    f"Duplicate lot id '{info.id}' in '{self.POOL.id}' lot infos"
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

        log(f"requesting {method} {url} {kwargs}")
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
    def convert_date(
            cls,
            date_string: str,
            date_format: str,
            timezone: Optional[str] = None
    ) -> str:
        """
        Convert a date into a ISO formatted UTC date string.
        Timezone defaults to Europe/Berlin.

        :param date_string: str, the date string
        :param date_format: str, the format for parsing the date string
        :param timezone: str|None, the timezone of the parsed date
        :return: str, iso-formatted string
        """
        if timezone is None:
            timezone = cls.POOL.timezone

        last_updated = datetime.datetime.strptime(date_string, date_format)
        local_timezone = pytz.timezone(timezone)
        last_updated = local_timezone.localize(last_updated, is_dst=None)
        last_updated = last_updated.astimezone(pytz.utc).replace(tzinfo=None)

        return last_updated.replace(microsecond=0).isoformat()
