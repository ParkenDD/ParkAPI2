"""
Original code by Kliemann
"""
import urllib.parse
from typing import List

from util import *


class Dresden(ScraperBase):

    POOL = PoolInfo(
        id="dresden",
        name="Dresden",
        public_url="https://www.dresden.de/parken",
        source_url="https://www.dresden.de/apps_ext/ParkplatzApp/",
    )

    def get_lot_data(self) -> List[LotData]:
        now = self.now()
        soup = self.request_soup(self.POOL.source_url)

        last_updated = None
        for h3 in soup.find_all("h3"):
            if h3.text == "Letzte Aktualisierung":
                last_updated = self.to_utc_datetime(h3.find_next_sibling("div").text, "%d.%m.%Y %H:%M:%S")

        lots = []
        for table in soup.find_all("table"):
            thead = table.find("thead")
            if not thead:
                continue
            region = table.find("thead").find("tr").find_all("th")[1].find("div").text

            if region == "Busparkplätze":
                continue

            for tr in table.find("tbody").find_all("tr"):
                td = tr.find_all("td")
                name = tr.find("a").text

                try:
                    total = int(td[2].find_all("div")[1].text)
                except ValueError:
                    total = None
                try:
                    free = int(td[3].find_all("div")[1].text)
                    valid_free = True
                except ValueError:
                    valid_free = False
                    free = None
                if "park-closed" in td[0]["class"]:
                    state = LotData.Status.closed
                elif "blue" in td[0]["class"] and not valid_free:
                    state = LotData.Status.nodata
                else:
                    state = LotData.Status.open

                lots.append(
                    LotData(
                        timestamp=now,
                        lot_timestamp=last_updated,
                        id=f"dresden-{name}",
                        status=state,
                        num_free=free,
                        capacity=total,
                    )
                )

        return lots

    def get_lot_infos(self) -> List[LotInfo]:
        soup = self.request_soup(self.POOL.source_url)

        lots = []
        for table in soup.find_all("table"):
            thead = table.find("thead")
            if not thead:
                continue

            region = table.find("thead").find("tr").find_all("th")[1].find("div").text

            for tr in table.find("tbody").find_all("tr"):
                lot_url = urllib.parse.urljoin(self.POOL.source_url, tr.find("a").attrs["href"])

                try:
                    lots.append(self.get_lot_info_from_page(lot_url))
                except:
                    print("IN URL", lot_url)
                    raise

        return lots

    def get_lot_info_from_page(self, url: str) -> LotInfo:
        soup = self.request_soup(url)

        name = soup.find("h1").text.strip()

        h3s = soup.find("div", class_="contentsection").find_all("h3")

        try:
            capacity = int(h3s[0].find_next_sibling("div", class_="row").find_all("div")[1].text)
        except ValueError:
            capacity = None

        address = get_soup_text(h3s[1].find_next_sibling("div")).replace(", ", "\n")

        lon, lat = None, None
        coord_rows = h3s[1].find_next_siblings("div", class_="row")
        if coord_rows:
            lon, lat = (
                float_or_none(coord_rows[0].find_all("div")[1].text),
                float_or_none(coord_rows[1].find_all("div")[1].text),
            )

        type = guess_lot_type(name)
        if name.endswith("Bus"):
            type = LotInfo.Types.bus
        short_name = " ".join(name.split()[1:])

        return LotInfo(
            id=f"dresden-{short_name}",
            name=short_name,
            type=type,
            capacity=capacity,
            has_live_capacity=True,
            address=address,
            latitude=lat,
            longitude=lon,
            public_url=url,
        )
