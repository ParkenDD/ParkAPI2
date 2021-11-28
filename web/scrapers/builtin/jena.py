import urllib.parse
from typing import List

from util import *


class Jena(ScraperBase):

    POOL = PoolInfo(
        id="jena",
        name="Jena",
        public_url="https://mobilitaet.jena.de/de/parken",
    )

    def get_lot_data(self) -> List[LotData]:
        now = self.now()
        soup = self.request_soup(self.POOL.public_url)
        lots = []

        div = soup.find("div", {"class": "view-parking-areas"})
        if not div:
            div = soup.find("div", {"class": "view-list-parkplaetze"})
        for tr in div.find("table").find_all("tr"):
            row = [td.text.strip() for td in tr.find_all("td")]

            if row and row[3] != "nie":
                lots.append(
                    LotData(
                        id=f"jena-{row[0]}",
                        timestamp=now,
                        status=LotData.Status.open,
                        num_free=int_or_none(row[1]),
                        capacity=int_or_none(row[2]),
                    )
                )

        return lots

    def get_lot_infos(self) -> List[LotInfo]:
        soup = self.request_soup(self.POOL.public_url)

        lots = []
        for div in soup.find_all("div", class_="geolocation-location"):
            content_rows = [
                [
                    d.find("span", class_="views-label").text.strip() if d.find("span", class_="views-label") else None,
                    d.find("span", class_="field-content") or d.find("div", class_="field-content"),
                ]
                for d in div.find_all("div", class_="views-field")
            ]

            name = content_rows[0][1].text.strip()

            lots.append(
                LotInfo(
                    id=f"jena-{name}",
                    name=name,
                    type=LotInfo.Types.unknown,
                    public_url=urllib.parse.urljoin(self.POOL.public_url, content_rows[0][1].find("a")["href"]),
                    source_url=self.POOL.public_url,
                    latitude=div["data-lat"],
                    longitude=div["data-lng"],
                    capacity=int_or_none(content_rows[2][1].text),
                    has_live_capacity=True,
                )
            )

        return lots
