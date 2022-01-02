"""
Original code and data by Woltmann, Quint, Koeltzsch,
"""
import urllib.parse
from typing import List, Tuple, Generator

from util import *


class Konstanz(ScraperBase):

    POOL = PoolInfo(
        id="konstanz",
        name="Konstanz",
        public_url="https://www.konstanz.de/start/leben+in+konstanz/parkleitsystem.html",
        source_url=None,
        timezone="Europe/Berlin",
        attribution_contributor="Stadt Konstanz",
        attribution_license=None,
        attribution_url=None,
    )

    def get_lot_data(self) -> List[LotData]:
        lots = []
        for lot_name, url in self.iter_lot_page_urls():

            timestamp = self.now()
            soup = self.request_soup(url)

            status = LotData.Status.nodata
            num_free = None
            capacity = None

            table = soup.find("table", class_="tablestandard plstabelle")
            for tr in table.find_all("tr"):
                if not tr.find("th"):
                    continue

                row_name = tr.find("th").text.strip()
                row_value = tr.find("td").text.strip()

                if row_name == "Parkplätze":
                    capacity = int_or_none(row_value)
                    if capacity:
                        status = LotData.Status.open
                elif row_name == "Freie Parkplätze":
                    num_free = int_or_none(row_value)

            lots.append(
                LotData(
                    timestamp=timestamp,
                    id=name_to_legacy_id("konstanz", lot_name),
                    status=status,
                    num_free=num_free,
                    capacity=capacity,
                )
            )

        return lots

    def get_lot_infos(self) -> List[LotInfo]:
        lot_map = {
            lot.name: lot
            for lot in self.get_v1_lot_infos_from_geojson("Konstanz")
        }

        lots = []
        for lot_name, url in self.iter_lot_page_urls():
            soup = self.request_soup(url)

            p = soup.find("section", id="content")
            text = get_soup_text(p)

            try:
                text = text[text.index("Adresse:")+9:]
                address = text[:text.index("Betreiber:")].strip()
            except ValueError:
                address = None

            kwargs = vars(lot_map[lot_name])
            kwargs["has_live_capacity"] = True
            if address:
                kwargs["address"] = address

            lots.append(LotInfo(**kwargs))

        return lots

    def iter_lot_page_urls(self) -> Generator[Tuple[str, str], None, None]:
        soup = self.request_soup(self.POOL.public_url)

        for table in soup.find_all("table", class_="parken"):
            for a in table.find_all("a"):
                url = urllib.parse.urljoin(self.POOL.public_url, a["href"])
                if url == self.POOL.public_url:
                    continue

                yield a.text.strip(), url
