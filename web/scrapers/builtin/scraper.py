import os
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
from typing import Union, Optional, Tuple, List, Type, Dict

import requests
from bs4 import BeautifulSoup


VERSION = (0, 0, 1)


def log(*args, **kwargs):
    print(datetime.datetime.now(), *args, **kwargs, file=sys.stderr)


class ScraperBase:

    CACHE_DIR = Path(tempfile.gettempdir()) / "scraper"
    REQUESTS_PER_SECOND = 10.

    POOL_ID = None
    TIMEZONE = "Europe/Berlin"

    __last_request_time = 0

    def __init__(
            self,
            caching: Union[bool, str] = False,
    ):
        """
        :param caching: bool|str
            Enable file-caching, can be True, False, "read" or "write"

        :param caching:
        """
        self.caching = caching
        self.session = requests.Session()
        self.session.headers = {
            "User-Agent": "github.com/defgsus/ParkAPI2",
        }

    def scrape(self) -> dict:
        raise NotImplementedError

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

        caching = self.caching if caching is None else caching

        cache_name = None
        if caching:
            cache_name = hashlib.md5(f"{method} {url} {kwargs}".encode("utf-8")).hexdigest()
            cache_name = self.CACHE_DIR / self.POOL_ID / f"{cache_name}.pkl"
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
            os.makedirs(str(self.CACHE_DIR / self.POOL_ID), exist_ok=True)
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
    def now(cls) -> str:
        """
        Return current datetime as UTC isoformat
        """
        return datetime.datetime.utcnow().replace(microsecond=0).isoformat()

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
            timezone = cls.TIMEZONE

        last_updated = datetime.datetime.strptime(date_string, date_format)
        local_timezone = pytz.timezone(timezone)
        last_updated = local_timezone.localize(last_updated, is_dst=None)
        last_updated = last_updated.astimezone(pytz.utc).replace(tzinfo=None)

        return last_updated.replace(microsecond=0).isoformat()

    @classmethod
    def get_all_scrapers(self) -> Dict[str, Type["ScraperBase"]]:
        self_filename = Path(__file__).resolve()
        scrapers_path = self_filename.parent

        scrapers = dict()
        for filename in glob.glob(str(scrapers_path / "*.py")):
            if filename != str(self_filename):
                module_name = Path(filename).name[:-3]
                module = importlib.import_module(module_name)
                for key, value in vars(module).items():
                    if getattr(value, "POOL_ID", None):

                        if value.POOL_ID in scrapers:
                            raise ValueError(
                                f"POOL_ID '{value.POOL_ID}' of class {value.__name__}"
                                f" is already used by class {scrapers[value.POOL_ID].__name__}"
                            )
                        scrapers[value.POOL_ID] = value

        return scrapers


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
        raise ValueError  # argparse would not display the exception message

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command", type=str,
        choices=["list", "scrape"],
        help="The command to execute",
    )
    parser.add_argument(
        "-c", "--cache", nargs="?", type=cache_type, default=False, const=True,
        help=f"Enable caching of the web-requests. Specify '-c' to enable writing and reading cache"
             f", '-c read' to only read cached files or '-c write' to only write cache files"
             f" but not read them. Cache directory is {ScraperBase.CACHE_DIR}"
    )

    return vars(parser.parse_args())


def main(
        command: str,
        cache: Union[bool, str],
):
    scrapers = ScraperBase.get_all_scrapers()
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
            scraper = scrapers[pool_id](caching=cache)
            log(f"scraping pool '{pool_id}'")
            data = scraper.scrape()
            print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main(**parse_args())
