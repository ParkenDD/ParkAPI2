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


VERSION = (0, 0, 1)

MODULE_DIR: Path = Path(__file__).resolve().parent


def log(*args, **kwargs):
    print(datetime.datetime.now(), *args, **kwargs, file=sys.stderr)


class PoolInfo:

    def __init__(
            self,
            id: str,
            name: str,
            web_url: str,
            timezone: str = "Europe/Berlin",
            source_url: Optional[str] = None,
            license: Optional[str] = None,
    ):
        self.id = id
        self.name = name
        self.web_url = web_url
        self.timezone = timezone
        self.source_url = source_url or None
        self.license = license or None


class LotInfo:

    def __init__(
            self,
            id: str,
            name: str,
            type: Optional[str] = None,
            web_url: Optional[str] = None,
            source_url: Optional[str] = None,
            address: Optional[str] = None,
            capacity: Optional[int] = None,
            has_live_capacity: bool = False,
            latitude: Optional[float] = None,
            longitude: Optional[float] = None,
    ):
        self.id = ScraperBase.name_to_id(id)
        self.name = name
        self.type = type
        self.web_url = web_url or None
        self.source_url = source_url or None
        self.address = address or None
        self.capacity = capacity
        self.has_live_capacity = has_live_capacity
        self.latitude = latitude
        self.longitude = longitude

        if self.type is None:
            name = self.name.lower()
            if "parkplatz" in name:
                self.type = "lot"
            elif "parkhaus" in name:
                self.type = "garage"
            elif "tiefgarage" in name:
                self.type = "underground"
            elif "parkdeck" in name:
                self.type = "level"
            else:
                raise ValueError(
                    f"Can not guess the type of lot '{self.name}', please specify with 'type'"
                )

    @classmethod
    def from_dict(cls, data: dict) -> "LotInfo":
        kwargs = {
            key: data[key]
            for key in [
                "id", "name", "type", "web_url", "source_url", "address",
                "capacity", "has_live_capacity",
                "latitude", "longitude",
            ]
            if key in data
        }
        return cls(**kwargs)


class LotData:

    class Status:
        open = "open"           # it's listed as open
        closed = "closed"       # it's listed as closed
        unknown = "unknown"     # status is not listed
        nodata = "nodata"       # whether num_free or num_occupied is not listed
        error = "error"         # http connection error or similar

    def __init__(
            self,
            timestamp: datetime.datetime,
            id: str,
            status: str,
            num_free: Optional[int] = None,
            num_occupied: Optional[int] = None,
            capacity: Optional[int] = None,
            lot_timestamp: Optional[datetime.datetime] = None
    ):
        self.id = ScraperBase.name_to_id(id)
        self.timestamp = timestamp
        self.status = status
        self.num_free = num_free
        self.num_occupied = num_occupied
        self.capacity = capacity
        self.lot_timestamp = lot_timestamp

        if self.status.startswith("_") or status not in vars(self.Status):
            raise ValueError(
                f"Lot '{self.id}' status must be one of %s" % (
                    ", ".join(key for key in vars(self.Status) if not key.startswith("_"))
                )
            )

        if self.capacity is not None:

            if self.num_free is not None:
                if self.num_occupied is None:
                    self.num_occupied = self.capacity - self.num_free
                else:
                    if self.num_occupied != self.capacity - self.num_free:
                        raise ValueError(
                            f"Lot '{self.id}' has invalid 'num_occupied' {self.num_occupied}"
                            f", expected {self.capacity - self.num_free}"
                            f" (free={self.num_free}, capacity={self.capacity})"
                        )

            elif self.num_occupied is not None:
                if self.num_free is None:
                    self.num_free = self.capacity - self.num_occupied
                else:
                    if self.num_free != self.capacity - self.num_occupied:
                        raise ValueError(
                            f"Lot '{self.id}' has invalid 'num_free' {self.num_free}"
                            f", expected {self.capacity - self.num_occupied}"
                            f" (occupied={self.num_occupied}, capacity={self.capacity})"
                        )


class ScraperBase:

    CACHE_DIR = Path(tempfile.gettempdir()) / "parkapi-scraper"
    REQUESTS_PER_SECOND = 2.
    USER_AGENT = "github.com/defgsus/ParkAPI2"

    # A PoolInfo object must be specified for each derived scraper
    POOL: PoolInfo = None

    # Will contain the geojson data if present
    GEOJSON: Optional[dict] = None

    # ---- internals ----

    __last_request_time = 0
    _re_double_minus = re.compile(r"--+")

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
        infos = []
        if self.GEOJSON:
            for feature in self.GEOJSON["features"]:
                lot_info = feature["properties"].copy()

                if feature.get("geometry"):
                    if feature["geometry"]["type"] != "Point":
                        raise ValueError(
                            f"""geometry type '{feature["geometry"]["type"]}' for lot '{lot_info["id"]}' not supported"""
                        )
                    lot_info["latitude"] = feature["geometry"][1]
                    lot_info["longitude"] = feature["geometry"][0]

                infos.append(LotInfo.from_dict(lot_info))
        return infos

    def get_lot_info_map(self) -> Dict[str, LotInfo]:
        lot_infos = self.get_lot_infos()
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

    @classmethod
    def remove_special_chars(cls, name: str) -> str:
        """
        Remove any umlauts, spaces and punctuation from a string.
        """
        replacements = {
            "ä": "ae",
            "ö": "oe",
            "ü": "ue",
            "ß": "ss",
            "-": "",
            " ": "",
            ".": "",
            ",": "",
            "'": "",
            "\"": "",
            "/": "",
            "\\": "",
            "\n": "",
            "\t": ""
        }
        for repl in replacements.keys():
            name = name.replace(repl, replacements[repl])
        return name

    @classmethod
    def name_to_id(cls, name: str) -> str:
        """
        Converts any string to
          - ascii alphanumeric or "-" characters
          - no spaces
          - lowercase
          - maximal length of 64
        """
        id_name = str(name)
        id_name = id_name.replace("ß", "ss")
        id_name = unicodedata.normalize('NFKD', id_name).encode("ascii", "ignore").decode("ascii")

        id_name = "".join(
            c if c.isalnum() or c in " \t" else "-"
            for c in id_name
        ).replace(" ", "-")

        id_name = cls._re_double_minus.sub("-", id_name).strip("-")
        return id_name.lower()[:64]

    @classmethod
    def int_or_none(cls, x) -> Optional[int]:
        try:
            x = str(x)
            if len(x) > 1:
                x = x.lstrip("0")
            return int(x)
        except (ValueError, TypeError):
            return None

    @classmethod
    def float_or_none(cls, x) -> Optional[float]:
        try:
            return float(str(x))
        except (ValueError, TypeError):
            return None


class SnapshotMaker:

    def __init__(self, scraper: ScraperBase):
        self.scraper = scraper

    def info_map_to_geojson(self) -> dict:
        info_map = self.scraper.get_lot_info_map()
        ret_data = {
            "type": "FeatureCollection",
            "features": []
        }
        for info in info_map.values():
            info = vars(info).copy()
            lat, lon = info.pop("latitude", None), info.pop("longitude", None)
            feature = {
                "type": "Feature",
                "properties": info,
            }
            if not (lat is None or lon is None):
                feature["geometry"] = {
                    "type": "Point",
                    "coordinates": [lon, lat]
                }
            ret_data["features"].append(feature)
        return ret_data

    def get_snapshot(self) -> List[dict]:
        info_map = self.scraper.get_lot_info_map()
        lots = []
        for lot_data in self.scraper.get_lot_data():
            if lot_data.id in info_map:
                merged_lot = vars(info_map[lot_data.id])
            else:
                merged_lot = dict()

            for key, value in vars(lot_data).items():
                if key not in merged_lot or value is not None:
                    merged_lot[key] = value

            if "timestamp" in merged_lot:
                merged_lot["timestamp"] = merged_lot["timestamp"].isoformat()
            lots.append(merged_lot)
        return lots


def parse_args() -> dict:

    def cache_type(a) -> Union[bool, str]:
        if isinstance(a, str):
            a = a.lower()
        if a == "true":
            return True
        elif a == "false":
            return False
        elif a in ("read", "write"):
            return a
        raise ValueError  # argparse does not display the exception message

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "command", type=str,
        choices=["list", "scrape", "store-geojson"],
        help="The command to execute",
    )
    parser.add_argument(
        "-p", "--pools", nargs="+", type=str,
        help=f"Filter for one or more pool IDs"
    )
    parser.add_argument(
        "-c", "--cache", nargs="?", type=cache_type, default=False, const=True,
        help=f"Enable caching of the web-requests. Specify '-c' to enable writing and reading cache"
             f", '-c read' to only read cached files or '-c write' to only write cache files"
             f" but not read them. Cache directory is {ScraperBase.CACHE_DIR}"
    )

    return vars(parser.parse_args())


def get_scrapers(
        pool_filter: List[str],
) -> Dict[str, Type["ScraperBase"]]:

    scrapers = dict()
    for filename in glob.glob(str(MODULE_DIR / "*.py")):
        module_name = Path(filename).name[:-3]
        if module_name == "scraper":
            continue

        module = importlib.import_module(module_name)
        for key, value in vars(module).items():
            if not inspect.isclass(value) or not getattr(value, "POOL", None):
                continue

            if value.POOL.id in scrapers:
                raise ValueError(
                    f"class {value.__name__}.POOL.id '{value.POOL.id}'"
                    f" is already used by class {scrapers[value.POOL.id].__name__}"
                )

            if pool_filter and value.POOL.id not in pool_filter:
                continue

            geojson_file = Path(filename[:-3] + ".geojson")
            if geojson_file.exists():
                value.GEOJSON = json.loads(geojson_file.read_text())

            scrapers[value.POOL.id] = value

    return scrapers


def main(
        command: str,
        cache: Union[bool, str],
        pools: List[str],
):
    scrapers = get_scrapers(pool_filter=pools)
    pool_ids = sorted(scrapers)

    if command == "list":
        if not pool_ids:
            print("No scrapers found")
            return

        max_length = max(len(i) for i in pool_ids)
        for pool_id in pool_ids:
            print(f"{pool_id:{max_length}}: class {scrapers[pool_id].__name__}")

    elif command == "scrape":

        for pool_id in pool_ids:
            log(f"scraping pool '{pool_id}'")
            scraper = scrapers[pool_id](caching=cache)
            snapshot = SnapshotMaker(scraper)
            data = snapshot.get_snapshot()
            print(json.dumps(data, indent=2, ensure_ascii=False))

    elif command == "store-geojson":

        for pool_id in pool_ids:
            log(f"scraping pool '{pool_id}'")
            scraper = scrapers[pool_id](caching=cache)
            snapshot = SnapshotMaker(scraper)
            data = snapshot.info_map_to_geojson()

            print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main(**parse_args())
