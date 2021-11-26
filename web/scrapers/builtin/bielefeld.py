import re
import urllib.parse
from typing import List

from util import *


class Bielefeld(ScraperBase):

    POOL = PoolInfo(
        id="bielefeld",
        name="Bielefeld",
        public_url="https://www.bielefeld.de/de/sv/verkehr/parken/park/",

    )

    def get_lot_data(self) -> List[LotData]:
        now = self.now()
        soup = self.request_soup(self.POOL.public_url)

        capacity_re = re.compile(".* (\d+) Plätze.*")
        num_free_re = re.compile(".* (\d+) frei.*")

        lots = []
        for table in soup.find_all("table"):

            # Don't need the ones without live data
            if "Parkleitsystem" not in str(table):
                continue

            for tr in table.find_all("tr"):
                text = tr.text.strip().replace("\n", " ")
                if text.startswith("Kapazität"):

                    status = LotData.Status.unknown
                    capacity = capacity_re.match(text)
                    if capacity:
                        capacity = int_or_none(capacity.groups()[0])

                    if "geschlossen" in text:
                        status = LotData.Status.closed
                        num_free = None
                    else:
                        num_free = num_free_re.match(text)
                        if num_free:
                            num_free = int_or_none(num_free.groups()[0])
                        if num_free is not None:
                            status = LotData.Status.open

                    h3 = table.parent.find("h3")
                    lot_id = h3["id"][3:]

                    lots.append(
                        LotData(
                            timestamp=now,
                            id=f"bielefeld-{lot_id}",
                            status=status,
                            num_free=num_free,
                            capacity=capacity,
                        )
                    )

        return lots

    def get_lot_infos(self) -> List[LotInfo]:
        soup = self.request_soup(self.POOL.public_url)

        capacity_re = re.compile(".* (\d+) Plätze.*")

        lots = []
        for table in soup.find_all("table"):
            for tr in table.find_all("tr"):
                text = tr.text.strip().replace("\n", " ")
                if text.startswith("Kapazität"):

                    capacity = capacity_re.match(text)
                    if capacity:
                        capacity = int_or_none(capacity.groups()[0])

                    h3 = table.parent.find("h3")
                    lot_id = h3["id"][3:]
                    name = h3.text.split("(")[0].strip()

                    address = h3.find_next_sibling("div").text.strip()
                    href = h3.parent.find("a")["href"]
                    coords = href[href.index("?map=")+5:href.index(",EPSG")]
                    _, lon, lat = coords.split(",")

                    if address.startswith("Zufahrten "):
                        address = address[10:]
                    elif address.startswith("Zufahrt "):
                        address = address[8:]
                    if address.startswith("über "):
                        address = address[5:]

                    lots.append(
                        LotInfo(
                            id=f"bielefeld-{lot_id}",
                            name=name,
                            type=guess_lot_type(name) or LotInfo.Types.unknown,
                            public_url=self.POOL.public_url,
                            address=address,
                            has_live_capacity=True,
                            capacity=capacity,
                            latitude=lat,
                            longitude=lon,
                        )
                    )

        return lots
