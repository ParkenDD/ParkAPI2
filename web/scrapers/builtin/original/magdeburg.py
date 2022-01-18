"""
Original code and data by Kliemann, Quint

Removed parsing of the second table as they do not provide
free numbers but only total capacity (at least, that's what
i think).
No "Endstelle Diesdorf", "Milchhof" and "Lange Lake" anymore.
"""
from typing import List

from util import *


class Magdeburg(ScraperBase):

    POOL = PoolInfo(
        id="magdeburg",
        name="Magdeburg",
        public_url="https://www.magdeburg.de/",
        source_url="https://www.movi.de/parkinfo/uebersicht.shtml",
        timezone="Europe/Berlin",
        attribution_contributor="ifak e.V. Magdeburg",
        attribution_license=None,
        attribution_url="https://www.movi.de/service/copyright.shtml",
    )

    def get_lot_data(self) -> List[LotData]:
        timestamp = self.now()
        soup = self.request_soup(self.POOL.source_url)

        lots = []

        # find all entries
        outer_table = soup.find('table')
        # first group of lots
        inner_tables = outer_table.find_all('table')
        # inner_tables[0] ist Navi-Leiste, weiter mit first_part[1]
        rows = inner_tables[1].find_all('tr')
        for row in rows[6:] :
            one_row = row.find_all('td')
            if one_row[0].text == '':
                continue

            if len(one_row) <= 5:
                startingPoint = 0
            else:
                startingPoint = 1
            parking_name = one_row[startingPoint+0].text.strip()

            last_updated = None
            try:
                last_updated = self.to_utc_datetime(one_row[startingPoint+4].text.strip(), "%d.%m.%Y %H:%M Uhr")
            except (ValueError, IndexError) as e:
                pass

            try:
                parking_free = None
                if 'offline' == one_row[startingPoint+1].text.strip():
                    parking_status = 'nodata'
                else:
                    parking_status = 'open'
                    parking_free = int(one_row[startingPoint+1].text)
            except:
                parking_status = 'nodata'
                parking_free = None

            lots.append(
                LotData(
                    timestamp=timestamp,
                    lot_timestamp=last_updated,
                    id=name_to_legacy_id("magdeburg", parking_name),
                    status=parking_status,
                    num_free=parking_free,
                )
            )

        return lots

    def get_lot_infos(self) -> List[LotInfo]:
        lot_map = {
            lot.name: lot
            for lot in self.get_v1_lot_infos_from_geojson("Magdeburg")
        }

        soup = self.request_soup(self.POOL.source_url)

        lots = []

        # find all entries
        outer_table = soup.find('table')
        # first group of lots
        inner_tables = outer_table.find_all('table')
        # inner_tables[0] ist Navi-Leiste, weiter mit first_part[1]
        rows = inner_tables[1].find_all('tr')
        for row in rows[6:] :
            one_row = row.find_all('td')
            if one_row[0].text == '':
                continue

            if len(one_row) <= 5:
                startingPoint = 0
            else:
                startingPoint = 1
            parking_name = one_row[startingPoint+0].text.strip()

            kwargs = vars(lot_map[parking_name])

            kwargs.update(dict(
                has_live_capacity=True,
                public_url=one_row[startingPoint+0].find("a")["href"].replace("http://", "https://")
            ))

            lots.append(LotInfo(**kwargs))

        return lots