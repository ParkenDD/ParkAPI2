import urllib.parse
from typing import List

from util import *


class Bochum(ScraperBase):

    POOL = PoolInfo(
        id="bochum",
        name="Buchum",
        public_url="https://www.parken-in-bochum.de/parkhaeuser/",
        attribution_contributor="WirtschaftsEntwicklungsGesellschaft Bochum mbH",
    )

    def get_lot_data(self) -> List[LotData]:
        now = self.now()
        soup = self.request_soup(self.POOL.public_url)

        lots = []
        for lot_elem in soup.find_all("article", class_="lot"):
            lot_id = "bochum-" + lot_elem["data-uid"]

            num_free = None
            status = LotData.Status.unknown

            spaces = lot_elem.find("div", class_="spaces")
            if spaces:
                try:
                    num_free = int(spaces.text.strip().split()[0])
                    status = LotData.Status.open
                except:
                    pass

            details = lot_elem.find("div", class_="details")
            if details:
                if details.text.strip() == "Durchgängig geöffnet":
                    status = LotData.Status.open
                else:
                    short_info = details.find("span", class_="shortinfo").find("span", class_="time")
                    if short_info:
                        if short_info["data-closed"]:
                            status = LotData.Status.closed

            lots.append(
                LotData(
                    timestamp=now,
                    id=lot_id,
                    status=status,
                    num_free=num_free,
                )
            )

        return lots

    def get_lot_infos(self) -> List[LotInfo]:
        soup = self.request_soup(self.POOL.public_url)

        lots = []
        for lot_elem in soup.find_all("article", class_="lot"):
            lot_id = "bochum-" + lot_elem["data-uid"]

            lot_name = lot_elem.find("h3").text.strip()
            lat, lng = lot_elem["data-lat"], lot_elem["data-lng"]
            lot_url = urllib.parse.urljoin(self.POOL.public_url, lot_elem.find("a", class_="title")["href"])
            extra = self._get_lot_infos(lot_url)

            lots.append(
                LotInfo(
                    id=lot_id,
                    name=lot_name,
                    type=LotInfo.Types.garage if lot_name.startswith("PH") else LotInfo.Types.underground,
                    latitude=lat or None,
                    longitude=lng or None,
                    public_url=lot_url,
                    source_url=self.POOL.public_url,
                    address=extra["address"],
                    capacity=extra["capacity"],
                )
            )

        return lots

    def _get_lot_infos(self, url) -> dict:
        soup = self.request_soup(url)
        capacity = None

        h2 = soup.find("h2", class_="fa-info-circle")
        for section in h2.parent.parent.find_all("section"):
            text = section.text.strip()
            if text.startswith("Stellplätze:"):
                cap_text = text[13:].split(",", 1)[0]
                if cap_text.startswith("ca. "):
                    cap_text = cap_text[4:]
                capacity = int(cap_text)
                break

        return {
            "address": soup.find("h1").find_next_sibling("span").text.strip(),
            "capacity": capacity,
        }
