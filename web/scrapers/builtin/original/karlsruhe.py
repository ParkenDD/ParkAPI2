"""
Original code and data by Quint
"""
import re
import urllib.parse
from typing import List, Tuple, Generator, Optional

import bs4

from util import *


class Karlsruhe(ScraperBase):

    POOL = PoolInfo(
        id="karlsruhe",
        name="Karlsruhe",
        public_url="https://web1.karlsruhe.de/service/Parken/",
        source_url="",
        timezone="Europe/Berlin",
        attribution_contributor="Stadt Karlsruhe",
        attribution_license=None,
        attribution_url=None,
    )

    RE_LOT_SPACES = re.compile(r".* (\d+) freie Plätze von (\d+)")

    def get_lot_data(self) -> List[LotData]:
        lots = []
        for lot_name, page_url in self.iter_lot_page_urls():

            timestamp = self.now()
            soup = self.request_soup(page_url)

            div = soup.find("div", class_="parkhausschild")

            status_german = div.parent.find("h3").text.lower()
            if "geöffnet" in status_german:
                status = LotData.Status.open
            elif "geschlossen" in status_german:
                status = LotData.Status.closed
            else:
                status = LotData.Status.unknown

            match = self.RE_LOT_SPACES.match(div.text.replace("\n", " "))
            if match:
                num_free, num_total = (int(m) for m in match.groups())
                if num_total == 0:
                    status = LotData.Status.nodata
            else:
                num_free, num_total = None, None

            timestamp_text = div.parent.find("h3").next_sibling.next_sibling.text.strip()
            try:
                lot_timestamp = self.to_utc_datetime(
                    timestamp_text, "Der letzte Stand ist von %m.%d.%Y - %H:%M Uhr"
                )
            except ValueError:
                lot_timestamp = None

            lots.append(
                LotData(
                    timestamp=timestamp,
                    lot_timestamp=lot_timestamp,
                    id=name_to_legacy_id("karlsruhe", lot_name),
                    status=status,
                    num_free=num_free,
                    capacity=num_total,
                )
            )
        return lots

    def get_lot_infos(self) -> List[LotInfo]:
        lot_map = {
            lot.name: lot
            for lot in self.get_v1_lot_infos_from_geojson("Karlsruhe")
        }

        lots = []
        for lot_name, page_url in self.iter_lot_page_urls():
            soup = self.request_soup(page_url)

            div = soup.find("div", class_="parkhausschild")
            match = self.RE_LOT_SPACES.match(div.text.replace("\n", " "))
            if match:
                num_free, num_total = (int(m) for m in match.groups())
            else:
                num_free, num_total = None, None

            h4 = [e for e in soup.find_all("h4") if e.text == "Adresse Parkhaus"][0]
            address = get_soup_text(h4.find_next_sibling("p"))

            kwargs = vars(lot_map[lot_name])
            kwargs.update(dict(
                has_live_capacity=True,
                address=address,
                capacity=num_total or kwargs["capacity"],
                public_url=page_url,
            ))
            lots.append(LotInfo(**kwargs))

        return lots

    def iter_lot_page_urls(self, soup: Optional[bs4.BeautifulSoup] = None) -> Generator[Tuple[str, str], None, None]:
        if soup is None:
            soup = self.request_soup(self.POOL.public_url)

        for div in soup.find_all("div", class_="parkhaus"):
            a = div.find("a")
            yield a.text.strip(), urllib.parse.urljoin(self.POOL.public_url, a["href"])

