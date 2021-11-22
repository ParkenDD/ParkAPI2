import os
import time
import requests
import hashlib
import json
import sys
from pathlib import Path
from typing import Tuple, List, Optional, Union


class NominatimApi:
    """
    Simple wrapper around OSM Nominatim API

    - https://nominatim.org/release-docs/develop/api/
    - https://operations.osmfoundation.org/policies/nominatim/

    """

    REQUESTS_PER_SECOND = .8
    BASE_URL = "https://nominatim.openstreetmap.org"
    CACHE_DIR = Path(__file__).resolve().parent.parent / "cache" / "nominatim"

    _last_request_time = 0

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.session = requests.Session()
        self.session.headers = {
            "User-Agent": "github.com/defgsus/ParkAPI2",
            "Accept": "application/json",
        }

    def log(self, *args, **kwargs):
        if self.verbose:
            print(f"{self.__class__.__name__}:", *args, **kwargs, file=sys.stderr)

    def search(
            self,
            q: Optional[str] = None,
            street: Optional[str] = None,
            city: Optional[str] = None,
            state: Optional[str] = None,
            country: Optional[str] = None,
            postalcode: Optional[str] = None,
            format: str = "geojson",
            extratags: int = 0,
            addressdetails: int = 0,
            namedetails: int = 0,
            polygon_geojson: int = 0,
            countrycodes: Optional[List[str]] = None,
            exclude_place_ids: Optional[List[str]] = None,
            limit: int = 10,
            dedupe: int = 1,
            caching: Union[bool, str] = True,
            **kwargs,
    ) -> Union[dict, List[dict]]:
        """
        Search endpoint, see https://nominatim.org/release-docs/develop/api/Search/
        """
        EXPLICIT_PARAMS = ("street", "city", "state", "country", "postalcode")
        params = {
            "format": format,
            "addressdetails": addressdetails,
            "namedetails": namedetails,
            "extratags": extratags,
            "polygon_geojson": polygon_geojson,
            "limit": limit,
            "dedupe": dedupe,
        }
        if exclude_place_ids:
            params["exclude_place_ids"] = ",".join(str(i) for i in exclude_place_ids)
        if countrycodes:
            params["countrycodes"] = ",".join(countrycodes)

        if q:
            if any(locals().get(key) for key in EXPLICIT_PARAMS):
                raise ValueError(
                    f"""Can not combine 'q' query with any of {", ".join(f"'{k}'" for k in EXPLICIT_PARAMS)}"""
                )
            params["q"] = q
        else:
            for key in EXPLICIT_PARAMS:
                if locals().get(key):
                    params[key] = locals()[key]

        status, data = self.request(
            path="search",
            caching=caching,
            expected_status=200,
            params={**params, **kwargs},
        )
        return data

    def lookup(
            self,
            osm_ids: List[str],
            format: str = "geojson",
            extratags: int = 0,
            addressdetails: int = 0,
            namedetails: int = 0,
            polygon_geojson: int = 0,
            caching: Union[bool, str] = True,
            **kwargs,
    ) -> Union[dict, List[dict]]:
        """
        Lookup endpoint, see https://nominatim.org/release-docs/develop/api/Lookup/
        """
        status, data = self.request(
            path="lookup",
            caching=caching,
            expected_status=200,
            params={
                "osm_ids": ",".join(osm_ids),
                "format": format,
                "addressdetails": addressdetails,
                "namedetails": namedetails,
                "extratags": extratags,
                "polygon_geojson": polygon_geojson,
                **kwargs,
            }
        )
        return data

    def request(
            self,
            path: str,
            caching: Union[bool, str] = True,
            expected_status: Optional[int] = None,
            **kwargs,
    ) -> Tuple[int, Union[dict, list]]:
        """
        Generic request against API.

        Will throttle all requests to the REQUESTS_PER_SECOND value.

        :param path: str, the specific endpoint
        :param caching: bool|str, enable file-caching, can be True, False, "read" or "write"
        :param expected_status: int|None, Raises error when returned status differs
        :param kwargs: any arguments to requests.request() except "method" and "url"
        :return: tuple of status_code and data (int, dict|list)
            Status will be zero if loaded from cache
        """
        url = f"{self.BASE_URL}/{path}"

        # -- check file cache --

        cache_name = None
        if caching:
            cache_name = hashlib.md5(f"{url} {kwargs}".encode("utf-8")).hexdigest()
            cache_name = self.CACHE_DIR / f"{cache_name}.json"
        if caching in (True, "read"):
            if cache_name.exists():
                self.log(f"reading cache '{cache_name}'")
                return 0, json.loads(cache_name.read_text())

        # -- throttle requests --

        passed_time = time.time() - self._last_request_time
        if passed_time < 1. / self.REQUESTS_PER_SECOND:
            wait_time = 1. / self.REQUESTS_PER_SECOND - passed_time
            self.log(f"throttling requests, waiting {wait_time:.2f} sec")
            time.sleep(wait_time)
        self._last_request_time = time.time()

        self.log(f"requesting GET {url} {kwargs}")
        response = self.session.request(
            method="GET",
            url=url,
            **kwargs,
        )

        if expected_status is not None:
            if response.status_code != expected_status:
                raise IOError(
                    f"Unexpected status {response.status_code} for request {url} {kwargs}"
                    f"\n\nResponse: {response.content}"
                )

        try:
            data = response.json()
        except json.JSONDecodeError as e:
            raise IOError(
                f"JSONDecodeError: {e} for request {url} {kwargs}"
                f"\n\nResponse: {response.content}"
            )

        # -- store cache --

        if caching in (True, "write"):
            self.log(f"writing cache '{cache_name}'")
            os.makedirs(str(self.CACHE_DIR), exist_ok=True)
            cache_name.write_text(json.dumps(data, indent=2))

        return response.status_code, data
