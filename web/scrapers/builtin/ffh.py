import urllib.parse
from typing import List, Generator

from util import *


class FFHParking(ScraperBase):

    POOL = PoolInfo(
        id="ffh",
        name="HitRadio FFH Parkhaus-Info",
        public_url="https://www.ffh.de/verkehr/parkhaeuser.html",
        license=None,
        timezone="Europe/Berlin",
    )

    def get_lot_data(self) -> List[LotData]:
        lots = []
        for url in self._iter_city_urls():
            lots += self._get_lot_data(url)

        return lots

    def get_lot_infos(self) -> List[LotInfo]:
        lots = []
        for url in self._iter_city_urls():
            lots += self._get_lot_infos(url)

        return lots

    def _iter_city_urls(self) -> Generator[str, None, None]:
        soup = self.request_soup(self.POOL.public_url)
        for tr in soup.find("table", {"id": "trafficParkingTable"}).find_all("tr"):
            td = tr.find_all("td")[1]
            href = td.find("a")["href"]
            url = urllib.parse.urljoin(self.POOL.public_url, href)
            yield url

    def _get_lot_data(self, url: str):
        now = self.now()
        soup = self.request_soup(url)

        lots = []
        for tr in soup.find("table", {"id": "trafficParkingList"}).find_all("tr"):
            lot_id = tr.get("data-facilityid")
            if not lot_id:
                continue

            tds = list(filter(
                lambda tag: tag.name == "td",
                tr.children
            ))

            parking_place_name = tds[0].find("a").text.strip()

            num_free = None
            capacity = None
            lot_timestamp = None

            sub_table = tds[0].find("table")
            if sub_table:
                for sub_tr in sub_table.find_all("tr"):
                    tds = sub_tr.find_all("td")

                    if "Plätze insgesamt" in tds[0].text:
                        capacity = int(tds[1].text)
                    if "Stand:" in tds[0].text:
                        lot_timestamp = self.to_utc_datetime(tds[1].text.strip()[:17], "%d.%m.%Y, %H:%M")

            num_free_text = tds[1].text.strip()
            if num_free_text == "belegt":
                num_free = capacity
            else:
                try:
                    num_free = int(num_free_text)
                    status = LotData.Status.open
                except ValueError:
                    status = LotData.Status.closed if "geschlossen" in num_free_text else LotData.Status.unknown

            lots.append(
                LotData(
                    id=f"ffh-{lot_id}",
                    timestamp=now,
                    lot_timestamp=lot_timestamp,
                    status=status,
                    num_free=num_free,
                    capacity=capacity,
                )
            )

        return lots

    def _get_lot_infos(self, url: str):
        now = self.now()
        soup = self.request_soup(url)

        lots = []
        for tr in soup.find("table", {"id": "trafficParkingList"}).find_all("tr"):
            lot_id = tr.get("data-facilityid")
            if not lot_id:
                continue

            tds = list(filter(
                lambda tag: tag.name == "td",
                tr.children
            ))

            sub_table = tds[0].find("table")

            if sub_table:
                name = tds[0].find("a").text.strip()
            else:
                name = tds[0].find("b").text.strip()
            capacity = None
            address = None

            if sub_table:
                for sub_tr in sub_table.find_all("tr"):
                    tds = sub_tr.find_all("td")

                    if "Plätze insgesamt" in tds[0].text:
                        capacity = int(tds[1].text)
                    if "Anfahrt:" in tds[0].text:
                        address = tds[1].text.strip()

            lots.append(
                LotInfo(
                    id=f"ffh-{lot_id}",
                    name=name,
                    type=guess_lot_type(name) or LotInfo.Types.unknown,
                    has_live_capacity=True,
                    capacity=capacity,
                    public_url=url,
                    address=address,
                )
            )

        return lots
