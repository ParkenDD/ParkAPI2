"""
Original code and data by Quint
"""
import warnings
from typing import List

from util import *


class Hanau(ScraperBase):

    POOL = PoolInfo(
        id="hanau",
        name="Hanau",
        public_url="https://erleben.hanau.de/reise/parken/index.html",
        source_url="https://erleben.hanau.de/reise/parken/072752/index.html",
        timezone="Europe/Berlin",
        attribution_contributor="Stadt Hanau",
        attribution_license=None,
        attribution_url=None,
    )

    @classmethod
    def normalize_lot_name(cls, name: str) -> str:
        """
        Change the names that are displayed by website
        to the names as they were a long time ago..
        :param name:
        :return:
        """
        return (
            name
            .replace("ue", "ü")
            .replace("oe", "ö")
            .replace("ae", "ä")
            .replace("trasse", "traße")
            .replace("Congress park", "Congress Park")
            .replace("Main Kinzig Halle", "Main-Kinzig-Halle")
        )

    def get_lot_data(self) -> List[LotData]:
        timestamp = self.now()
        soup = self.request_soup(self.POOL.source_url)

        lots = []

        parking_data = soup.find('div', class_='container-fluid')
        last_updated = self.to_utc_datetime(parking_data.find('h5').text, 'Letzte Aktualisierung: %d.%m.%Y %H:%M:%S')

        for one_parking_lot in parking_data.find_all('div', class_='well'):
            parking_name = self.normalize_lot_name(one_parking_lot.find('b').text.strip())

            parking_free = None
            try:
                parking_status = LotData.Status.open
                parking_free = int(one_parking_lot.find_all('div', role='progressbar')[1].find('b').text.strip())
            except:
                parking_status = LotData.Status.nodata

            capacity = None
            capacity_tag = one_parking_lot.find('span', class_='badge')
            if capacity_tag and "Plätze" in capacity_tag.text:
                capacity = int(capacity_tag.text.split()[0])

            # total space == 0 probably means it's offline right now
            if capacity == 0 and not parking_free:
                capacity = None
                parking_free = None
                parking_status = LotData.Status.nodata

            lots.append(
                LotData(
                    timestamp=timestamp,
                    lot_timestamp=last_updated,
                    id=name_to_legacy_id("hanau", parking_name),
                    num_free=parking_free,
                    capacity=capacity,
                    status=parking_status,
                )
            )

        return lots

    def get_lot_infos(self) -> List[LotInfo]:
        lot_map = {
            lot.name: lot
            for lot in self.get_v1_lot_infos_from_geojson("Hanau")
        }

        soup = self.request_soup(self.POOL.source_url)
        lots = []

        parking_data = soup.find('div', class_='container-fluid')
        for one_parking_lot in parking_data.find_all('div', class_='well'):
            parking_name = self.normalize_lot_name(one_parking_lot.find('b').text.strip())

            capacity = None
            capacity_tag = one_parking_lot.find('span', class_='badge')
            if capacity_tag and "Plätze" in capacity_tag.text:
                capacity = int(capacity_tag.text.split()[0])

            public_url = one_parking_lot.find("a", class_="hvr-icon-drop")["href"]

            if parking_name not in lot_map:
                warnings.warn(f"Lot '{parking_name}' not in original geojson")

            kwargs = vars(lot_map[parking_name]) if parking_name in lot_map else dict()
            kwargs.update(dict(
                id=name_to_legacy_id("hanau", parking_name),
                name=parking_name,
                capacity=capacity,
                has_live_capacity=True,
                public_url=public_url,
            ))
            lots.append(LotInfo(**kwargs))

        return lots
