"""
Original code and data by Quint
"""
import urllib.parse
from typing import List, Tuple, Generator

import bs4

from util import *


class Nuernberg(ScraperBase):

    POOL = PoolInfo(
        id="nuernberg",
        name="Nürnberg",
        public_url="https://tiefbauamt.nuernberg.de/site/parken/parkhausbelegung/parkhaus_belegung.html",
        source_url=None,
        timezone="Europe/Berlin",
        attribution_contributor="Stadt Nürnberg",
        attribution_license=None,
        attribution_url="https://www.nuernberg.de/",
    )

    def get_lot_data(self) -> List[LotData]:
        timestamp = self.now()
        soup = self.request_soup(self.POOL.public_url)

        lots = []

        date_time_text = soup.find('td', width='233').text.strip()
        last_updated = self.to_utc_datetime(date_time_text, 'Stand vom %d.%m.%Y, %H:%M:%S')

        for html_parkhaus_row, parking_name in self.iter_parkhaus_rows(soup):
            # one row: one parkhaus
            html_parkhaus_data = html_parkhaus_row.find_all('td')

            parking_state = LotData.Status.open
            parking_free = None
            capacity = int_or_none(html_parkhaus_data[3].text)
            try:
                parking_free = int(html_parkhaus_data[2].text)
            except:
                parking_state = LotData.Status.nodata

            lots.append(
                LotData(
                    timestamp=timestamp,
                    lot_timestamp=last_updated,
                    id=name_to_legacy_id("nuernberg", parking_name),
                    status=parking_state,
                    num_free=parking_free,
                    capacity=capacity,
                )
            )

        return lots

    def iter_parkhaus_rows(self, soup: bs4.BeautifulSoup) -> Generator[Tuple[bs4.PageElement, str], None, None]:
        """
        Yields for each parking lot the <tr> element and the name.

        :return: geneator of tuple(bs4.PageElement, str)
        """
        # everything is in table-objects
        # so we have to go down several levels of table-objects
        html_level0 = soup.find('table')
        html_level1 = html_level0.find_all( 'table')
        html_level2 = html_level1[1].find_all('table')
        html_level3 = html_level2[0].find_all('table')
        html_level4 = html_level3[2].find_all('table')
        # here we have the data of the tables
        #   [0]: header
        #   [1]: empty
        #   all following: empty or Parkhaus
        for html_parkhaus in html_level4[2:] :
            if html_parkhaus.text.strip() == '':
                continue   # table is empty
            html_parkhaus_all_rows = html_parkhaus.find_all('tr')
            for html_parkhaus_row in html_parkhaus_all_rows:

                html_parkhaus_data = html_parkhaus_row.find_all('td')
                parking_name_list = html_parkhaus_data[1].text.split()
                parking_name = ' '.join(parking_name_list)

                yield html_parkhaus_row, parking_name

    def get_lot_infos(self) -> List[LotInfo]:
        NEW_TO_LEGACY_NAME_MAP = {
            "Parkhaus Sebalder Höfe": "Parkhaus Sebalder-Höfe",
            # they seem to have expanded
            "Parkhaus Findelgasse": "Tiefgarage Findelgasse",
        }
        lot_map = {
            lot.name: lot
            for lot in self.get_v1_lot_infos_from_geojson("Nuernberg")
        }

        soup = self.request_soup(self.POOL.public_url)

        lots = []

        for html_parkhaus_row, parking_name in self.iter_parkhaus_rows(soup):
            html_parkhaus_data = html_parkhaus_row.find_all('td')

            public_url = None
            link = html_parkhaus_data[1].find("a")
            if link:
                urllib.parse.urljoin(self.POOL.public_url, link["href"])

            kwargs = vars(lot_map[NEW_TO_LEGACY_NAME_MAP.get(parking_name, parking_name)])
            kwargs.update(dict(
                public_url=public_url,
                has_live_capacity=True,
                # update the name changes
                name=parking_name,
                id=name_to_legacy_id("nuernberg", parking_name),
            ))

            lots.append(LotInfo(**kwargs))

        return lots
