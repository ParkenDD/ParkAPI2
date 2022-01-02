"""
Original code and data by Quint
"""
from typing import List

from util import *


class Limburg(ScraperBase):

    POOL = PoolInfo(
        id="limburg",
        name="Limburg",
        public_url="https://www.limburg.de/Verkehr/Parken",
        source_url="https://p127393.mittwaldserver.info/LM/_pls/pls.php",
        timezone="Europe/Berlin",
        attribution_contributor="Stadt Limburg",
        attribution_license=None,
        attribution_url=None,
    )

    def get_lot_data(self) -> List[LotData]:
        timestamp = self.now()
        soup = self.request_soup(self.POOL.source_url)

        last_updated = self.to_utc_datetime(soup.find('b').text, 'Stand: %d.%m.%Y %H:%M:%S Uhr')
        lots = []

        entries = soup.find('table', class_='tabellenformat')
        entries_rows = entries.find_all('tr')
        # first line: header
        for one_entry in entries_rows[1:]:
            one_entry_data = one_entry.find_all('td')
            if len(one_entry_data) < 6:
                continue

            parking_name = one_entry_data[0].text.strip()
            parking_free = None
            parking_total = None
            parking_status = LotData.Status.unknown

            if one_entry_data[5].text == 'Offen':
                parking_status = LotData.Status.open
            elif one_entry_data[5].text == 'Geschlossen':
                parking_status = LotData.Status.closed

            try:
                parking_total = int(one_entry_data[1].text)
                parking_free = int(one_entry_data[3].text)
            except:
                parking_status = LotData.Status.nodata

            # avoid storing zeros when lot is closed
            if parking_status == LotData.Status.closed:
                if not parking_free:
                    parking_free = None
                if not parking_total:
                    parking_total = None

            lots.append(
                LotData(
                    timestamp=timestamp,
                    lot_timestamp=last_updated,
                    id=name_to_legacy_id("limburg", parking_name),
                    status=parking_status,
                    num_free=parking_free,
                    capacity=parking_total,
                )
            )

        return lots

    def get_lot_infos(self) -> List[LotInfo]:
        return self.get_v1_lot_infos_from_geojson(
            "Limburg",
            defaults={
                "has_live_capacity": True,
            }
        )
