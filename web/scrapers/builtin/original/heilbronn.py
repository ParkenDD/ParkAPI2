"""
Original code and data by Quint
"""
from typing import List

from util import *


class Heilbronn(ScraperBase):

    POOL = PoolInfo(
        id="heilbronn",
        name="Heilbronn",
        public_url="https://www.heilbronn.de/umwelt-mobilitaet/mobilitaet/parken.html",
        source_url="https://www.heilbronn.de/allgemeine-inhalte/ajax-parkhausbelegung?type=1496993343",
        timezone="Europe/Berlin",
        attribution_contributor="Stadt Heilbronn",
        attribution_license=None,
        attribution_url=None,
    )

    def get_lot_data(self) -> List[LotData]:
        timestamp = self.now()
        soup = self.request_soup(self.POOL.source_url)

        lots = []

        last_updated = self.to_utc_datetime(
            soup.find('div', class_='col-sm-12').text,
            'Datum: %d.%m.%Y - Uhrzeit: %H:%M'
        )

        parking_lots = soup.find_all( 'div', class_='row carparkContent')
        for one_parking_lot in parking_lots:
            park_temp1 = one_parking_lot.find('div', class_='carparkLocation col-sm-9')
            park_temp2 = park_temp1.find('a')
            if park_temp2 != None:
                parking_name = park_temp2.text.strip()
            else:
                parking_name = park_temp1.text.strip()

            parking_free = None
            parking_state = LotData.Status.nodata
            try:
                # text: Freie Parkplätze: 195
                parking_free_temp = one_parking_lot.find('div', class_='col-sm-5').text.split()
                # parking_free_temp: ['Freie', 'Parkplätze:', '195']
                parking_free = int(parking_free_temp[2])
                parking_state = LotData.Status.open
            except:
                pass

            lots.append(
                LotData(
                    timestamp=timestamp,
                    lot_timestamp=last_updated,
                    id=name_to_legacy_id("heilbronn", parking_name),
                    status=parking_state,
                    num_free=parking_free,
                )
            )

        return lots

    def get_lot_infos(self) -> List[LotInfo]:
        lot_map = {
            lot.name: lot
            for lot in self.get_v1_lot_infos_from_geojson("Heilbronn")
        }

        lots = []

        soup = self.request_soup(self.POOL.source_url)
        parking_lots = soup.find_all( 'div', class_='row carparkContent')
        for one_parking_lot in parking_lots:
            park_temp1 = one_parking_lot.find('div', class_='carparkLocation col-sm-9')
            park_temp2 = park_temp1.find('a')
            if park_temp2 is not None:
                parking_name = park_temp2.text.strip()
            else:
                parking_name = park_temp1.text.strip()

            kwargs = vars(lot_map[parking_name])
            kwargs["public_url"] = park_temp2["href"] if park_temp2 else None

            lots.append(LotInfo(**kwargs))

        return lots
