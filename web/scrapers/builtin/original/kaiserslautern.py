"""
Original code and data by nicomue7
"""
import urllib.parse
from typing import List

from util import *


class Kaiserslautern(ScraperBase):

    POOL = PoolInfo(
        id="kaiserslautern",
        name="Kaiserslautern",
        public_url="https://www.kaiserslautern.de/sozial_leben_wohnen/verkehr_parken/autos_und_co/parken/index.html.de",
        source_url="https://www.kaiserslautern.de/live_tools/pls/pls.xml",
        timezone="Europe/Berlin",
        attribution_contributor="Stadt Kaiserslautern",
        attribution_license=None,
        attribution_url=None,
    )

    def get_lot_data(self) -> List[LotData]:
        timestamp = self.now()
        soup = self.request_soup(self.POOL.source_url)

        lots = []

        last_updated = self.to_utc_datetime(soup.find("zeitstempel").text)

        for ph in soup.find_all("parkhaus"):
            lot_name = ph.find("name").text
            lot_actual = int(ph.find("aktuell").text)
            lot_total = int(ph.find("gesamt").text)

            # please be careful about the state only being allowed to contain either open, closed or nodata
            # should the page list other states, please map these into the three listed possibilities
            # translate german state to english
            stateGerman = ph.find("status").text
            if stateGerman == ("Offen"):
                state = LotData.Status.open
            elif stateGerman == ("Geschlossen"):
                state = LotData.Status.closed
            else:
                state = LotData.Status.unknown

            lots.append(
                LotData(
                    timestamp=timestamp,
                    lot_timestamp=last_updated,
                    id=name_to_legacy_id("kaiserslautern", lot_name),
                    status=state,
                    num_occupied=lot_actual,
                    capacity=lot_total,
                )
            )
        return lots

    def get_lot_infos(self) -> List[LotInfo]:
        NAME_MAPPING = {
            "Lutrina Straße": "Lutrinastraße",
            "Meuthstraße I": "Meuthstraße Besucher",
            "Meuthstraße II": "Meuthstraße Angestellte",
        }
        # scrape the public_urls for each parking lot
        name_2_url_map = dict()
        soup = self.request_soup(self.POOL.public_url)
        for parking_block in soup.find_all("div", class_="parking_block"):
            for a in parking_block.find_all("a"):
                name = a.text.strip()
                name = NAME_MAPPING.get(name, name)
                name = f"PH {name}"
                name_2_url_map[name] = urllib.parse.urljoin(self.POOL.public_url, a["href"])

        # read original geojson
        lots = self.get_v1_lot_infos_from_geojson("Kaiserslautern", defaults={"has_live_capacity": True})

        # attach public_urls
        for lot in lots:
            lot.public_url = name_2_url_map[lot.name]

        return lots



