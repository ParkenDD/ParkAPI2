from typing import List

from util import *


class Apag(ScraperBase):

    POOL = PoolInfo(
        id="apag",
        name="Aachener Parkhaus GmbH",
        public_url="https://www.apag.de",
    )

    def get_lot_data(self) -> List[LotData]:
        lots = self._scrape_data("aachen", f"{self.POOL.public_url}/parken-in-aachen")
        lots += self._scrape_data("datteln", f"{self.POOL.public_url}/parken-in-datteln")
        return lots

    def get_lot_infos(self) -> List[LotInfo]:
        lots = self._scrape_lot_infos("aachen", f"{self.POOL.public_url}/parken-in-aachen")
        lots += self._scrape_lot_infos("datteln", f"{self.POOL.public_url}/parken-in-datteln")
        return lots

    def _scrape_data(self, id_prefix: str, url: str) -> List[LotData]:
        now = self.now()
        soup = self.request_soup(url)

        parking_name_set = set()

        lots = []

        parking_houses = soup.find_all('div', class_='houses')
        for parking_group in parking_houses:
            parking_lots = parking_group.find_all('li')
            for one_lot in parking_lots:
                parking_name = one_lot.find('a').text
                if parking_name not in parking_name_set:
                    parking_name_set.add(parking_name)

                    parking_state = 'open'
                    parking_free = None
                    try:
                        parking_free = int(one_lot.find('span', class_='free-text').text.split()[0])
                    except:
                        parking_state = 'nodata'

                    lots.append(
                        LotData(
                            timestamp=now,
                            id=f"{id_prefix}-{parking_name}",
                            num_free=parking_free,
                            status=parking_state,
                        )
                    )

        return lots

    def _scrape_lot_infos(self, id_prefix: str, url: str) -> List[LotInfo]:
        soup = self.request_soup(url)

        parking_name_set = set()

        lots = []

        parking_houses = soup.find_all('div', class_='houses')
        for parking_group in parking_houses:
            parking_lots = parking_group.find_all('li')
            for one_lot in parking_lots:
                parking_name = one_lot.find('a').text.strip()
                if parking_name not in parking_name_set:
                    parking_name_set.add(parking_name)

                    lot_url = self.POOL.public_url.rstrip("/") + one_lot.find("a").attrs["href"]
                    lot_soup = self.request_soup(lot_url)

                    elem_total = lot_soup.find("span", {"class": "total"})
                    elem_address = lot_soup.find("div", {"class": "address"})

                    elem_lat = lot_soup.find("meta", {"itemprop": "latitude"})
                    elem_lon = lot_soup.find("meta", {"itemprop": "longitude"})

                    type = guess_lot_type(parking_name)
                    name = " ".join(parking_name.split()[1:])

                    lots.append(
                        LotInfo(
                            id=f"{id_prefix}-{parking_name}",
                            name=name,
                            type=type,
                            public_url=lot_url,
                            source_url=url,
                            address="\n".join(l.strip() for l in elem_address.text.splitlines() if l.strip()),
                            capacity=int_or_none(elem_total.text.split()[-1]) if elem_total else None,
                            latitude=float_or_none(elem_lat.get("content")),
                            longitude=float_or_none(elem_lon.get("content"))
                        )
                    )

        return lots
