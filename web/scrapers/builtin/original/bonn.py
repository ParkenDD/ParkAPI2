"""
Original code and data by Thalheim, Kliemann, a.o.

Website seems to have changed completely since then so this is a rewrite.

"""
import urllib.parse
from typing import List, Tuple, Generator

import bs4

from util import *


class Bonn(ScraperBase):

    POOL = PoolInfo(
        id="bonn",
        name="Bonn",
        public_url="https://bcp-bonn.de/",
        source_url=None,
        timezone="Europe/Berlin",
        attribution_contributor=None,
        attribution_license=None,
        attribution_url=None,
    )

    def get_lot_data(self) -> List[LotData]:
        now = self.now()
        soup = self.request_soup(self.POOL.public_url)

        lots = []

        for div, free_spaces_tag in self.iter_parking_tags(soup):
            name = div.find("h5").text.strip()

            num_free = int_or_none(free_spaces_tag.find_next_sibling("strong").text)

            lots.append(
                LotData(
                    timestamp=now,
                    id=name_to_legacy_id("bonn", name),
                    num_free=num_free,
                    status=LotData.Status.open if isinstance(num_free, int) else LotData.Status.unknown,
                )
            )

        return lots

    def get_lot_infos(self) -> List[LotInfo]:
        """
        Careful! This works well enough but some google-maps links
        are wrong (lost in copy/paste parallel universe) so the
        resulting geojson is adjusted by hand!
        """
        soup = self.request_soup(self.POOL.public_url)

        lots = []

        for div, free_spaces_tag in self.iter_parking_tags(soup):
            title_tag = div.find("h5")
            name = title_tag.text.strip()
            lot_url = title_tag.find("a")["href"]

            lot_type = guess_lot_type(name)
            if not lot_type:
                if name.startswith("Charles de Gaulle Str"):
                    lot_type = LotInfo.Types.lot
                else:
                    raise ValueError(f"Can not guess lot-type for lot '{name}'")

            map_a = None
            for a in div.find_all("a"):
                if a["href"].startswith("https://www.google.de/maps/"):
                    map_a = a
                    break

            if not map_a:
                raise ValueError(f"map link not found for lot '{name}'")

            # extract address and geo-coords from google maps link
            map_link = map_a["href"].split("/")
            for i, ml in enumerate(map_link):
                if ml.startswith("@"):
                    map_link = map_link[i-1:]
                    break

            address = "\n".join(
                s.strip()
                for s in urllib.parse.unquote_plus(map_link[0]).split(",")
            )
            if address.startswith(name + "\n"):
                address = address[len(name)+1:]

            lat, lon = [float(c) for c in map_link[1][1:].split(",")[:2]]

            lots.append(
                LotInfo(
                    id=name_to_legacy_id("bonn", name),
                    name=name,
                    type=lot_type,
                    public_url=lot_url,
                    address=address,
                    latitude=lat,
                    longitude=lon,
                )
            )
            self.add_lot_page_info(lots[-1])

        return lots

    def iter_parking_tags(self, soup) -> Generator[Tuple[bs4.Tag, bs4.Tag], None, None]:
        name_set = set()
        for div in soup.find_all("div", {"class": "elementor-column"}):
            h5 = div.find("h5")
            if h5:
                a = h5.find("a")
                if a and a["href"].startswith("https://bcp-bonn.de/"):
                    name = h5.text.strip()
                    if name not in name_set:
                        name_set.add(name)

                        free_spaces_tag = None
                        for tag in div.find_all("strong"):
                            if tag.text and "Freie Stellplätze" in tag.text:
                                free_spaces_tag = tag
                                break

                        if free_spaces_tag:
                            yield div, free_spaces_tag

    def add_lot_page_info(self, lot: LotInfo):
        soup = self.request_soup(lot.public_url)

        for b in soup.find_all("b"):
            if b.text and b.text.strip() == "Einstellplätze:":
                lot.capacity = int_or_none(b.next_sibling)
