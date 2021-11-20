import os
import time
import requests
import hashlib
import json
from pathlib import Path
from typing import Tuple, List, Optional, Union


class NominatimApi:
    """
    Simple wrapper around OSM Nominatim API

    - https://nominatim.org/release-docs/develop/api/
    - https://operations.osmfoundation.org/policies/nominatim/

    """

    REQUEST_PER_SECOND = .8
    BASE_URL = "https://nominatim.openstreetmap.org"
    CACHE_DIR = Path(__file__).resolve().parent.parent / "cache" / "nominatim"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers = {
            "User-Agent": "github.com/defgsus/ParkAPI2",
            "Accept": "application/json",
        }
        self.last_request_time = 0

    def lookup(
            self,
            osm_ids: List[str],
            format: str = "geojson",
            extratags: int = 1,
            addressdetails: int = 1,
            polygon_geojson: int = 0,
            caching: Union[bool, str] = True,
            **kwargs,
    ) -> List[dict]:

        status, data = self.request(
            path="lookup",
            caching=caching,
            expected_status=200,
            params={
                "osm_ids": ",".join(osm_ids),
                "format": format,
                "addressdetails": addressdetails,
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

        Will throttle all requests to the REQUEST_PER_SECOND value.

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
                return 0, json.loads(cache_name.read_text())

        # -- throttle requests --

        passed_time = time.time() - self.last_request_time
        if passed_time < self.REQUEST_PER_SECOND:
            time.sleep(self.REQUEST_PER_SECOND - passed_time)

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
            os.makedirs(str(self.CACHE_DIR), exist_ok=True)
            cache_name.write_text(json.dumps(data, indent=2))

        return response.status_code, data
