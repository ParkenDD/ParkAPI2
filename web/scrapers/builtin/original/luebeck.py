"""
Original code and data by Thalheim

This is a rewrite, not using the original geojson!

Former urls were:
- http://www.kwl-luebeck.de/parken/aktuelle-parkplatzbelegung/
- http://kwlpls.adiwidjaja.info

both not working anymore.

New website supplies all meta information and the new geojson
is made from scratch.

The legacy IDs are kept as far as the lot name did not change.
"""
import urllib.parse
from typing import List

from util import *


class Luebeck(ScraperBase):

    POOL = PoolInfo(
        id="luebeck",
        name="Lübeck",
        public_url="https://www.parken-luebeck.de/",
        source_url=None,
        timezone="Europe/Berlin",
        attribution_contributor="KWL GmbH",
        attribution_license=None,
        attribution_url=None,
    )

    def get_lot_data(self) -> List[LotData]:
        timestamp = self.now()
        soup = self.request_soup(self.POOL.public_url)

        lots = []
        for lot_tag in soup.find("div", id="infos").find_all("div", class_="location-list--item"):

            free_tag = lot_tag.find("div", class_="free-live-spots")
            if not free_tag:
                continue

            num_free = int_or_none(free_tag.text)
            capacity = int_or_none(lot_tag.find("div", class_="free-spots").text.strip("/ "))
            lot_name = lot_tag["data-title"].split(" - ", 1)[0]
            status = LotData.Status.open

            if num_free is None:
                status = LotData.Status.nodata

            lots.append(
                LotData(
                    timestamp=timestamp,
                    id=name_to_legacy_id("luebeck", lot_name),
                    status=status,
                    num_free=num_free,
                    capacity=capacity,
                )
            )

        return lots

    def get_lot_infos(self) -> List[LotInfo]:
        soup = self.request_soup(self.POOL.public_url)

        lots = []
        for lot_tag in soup.find("div", id="infos").find_all("div", class_="location-list--item"):

            free_tag = lot_tag.find("div", class_="free-live-spots")
            if not free_tag:
                continue

            capacity = int_or_none(lot_tag.find("div", class_="free-spots").text.strip("/ "))
            lot_name = lot_tag["data-title"].split(" - ", 1)[0]

            public_url = urllib.parse.urljoin(self.POOL.public_url, lot_tag.find("a")["href"])

            lots.append(
                LotInfo(
                    id=name_to_legacy_id("luebeck", lot_name),
                    name=lot_name,
                    type=guess_lot_type(lot_tag["data-art"]),
                    capacity=capacity,
                    latitude=float_or_none(lot_tag["data-lat"]),
                    longitude=float_or_none(lot_tag["data-lng"]),
                    public_url=public_url,
                    has_live_capacity=True,
                    **self.get_lot_page_infos(public_url),
                )
            )

        return lots

    def get_lot_page_infos(self, url: str) -> dict:
        soup = self.request_soup(url)

        address = get_soup_text(soup.find("div", class_="long-parking-address"))
        if address.startswith("Adresse"):
            address = address[7:]
        address = address.strip()

        return {
            "address": address
        }
