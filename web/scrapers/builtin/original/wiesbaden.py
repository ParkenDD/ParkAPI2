"""
Original code and data by Quint
"""
import datetime
from typing import List, Tuple, Generator

from util import *


class Wiesbaden(ScraperBase):

    POOL = PoolInfo(
        id="wiesbaden",
        name="Wiesbaden",
        public_url="https://www.wiesbaden.de/leben-in-wiesbaden/verkehr/auto/parkhaeuser.php",
        # that's only part of it
        source_url="https://geoportal.wiesbaden.de/cgi-bin/mapserv.fcgi?map=d:/openwimap/umn/map/parkleitsystem/parkhaeuser.map&VERSION=1.3.0&service=WMS&request=GetFeatureInfo&version=1.1.1&layers=parkhaeuser&styles=&format=image%2Fpng&transparent=true&continuousWorld=true&tiled=true&info_format=text%2Fhtml&width=664&height=650&srs=EPSG%3A3857",
        timezone="Europe/Berlin",
        attribution_contributor="Stadt Wiesbaden",
        attribution_license=None,
        attribution_url=None,
    )

    # These url parameters are copied from the browser
    #   when clicking a lot on the map
    # This is a bit crude and only works as long as a lot
    #   does not change position (hehe)
    # And new lots will not be detected. They could be
    #   at least detected by the public_url's inline
    #   javascript objects. Have a look and then decide
    #   if this quick hack is too crude ;)
    LOT_URL_PARAMS = [
        "&bbox=915658.2710851978%2C6458475.045241954%2C918830.4077590327%2C6461580.299516035&query_layers=parkhaeuser&X=493&Y=116",
        "&bbox=915658.2710851978%2C6458475.045241954%2C918830.4077590327%2C6461580.299516035&query_layers=parkhaeuser&X=296&Y=176",
        "&bbox=915658.2710851978%2C6459688.48306598%2C918830.4077590327%2C6462793.737340063&query_layers=parkhaeuser&X=520&Y=430",
        "&bbox=915667.8257137334%2C6459688.48306598%2C918839.9623875683%2C6462793.737340063&query_layers=parkhaeuser&X=253&Y=461",
        "&bbox=915667.8257137334%2C6459688.48306598%2C918839.9623875683%2C6462793.737340063&query_layers=parkhaeuser&X=233&Y=484",
        "&bbox=915667.8257137334%2C6459688.48306598%2C918839.9623875683%2C6462793.737340063&query_layers=parkhaeuser&X=324&Y=505",
        "&bbox=915667.8257137334%2C6459688.48306598%2C918839.9623875683%2C6462793.737340063&query_layers=parkhaeuser&X=401&Y=520",
        "&bbox=915667.8257137334%2C6459688.48306598%2C918839.9623875683%2C6462793.737340063&query_layers=parkhaeuser&X=277&Y=580",
        "&bbox=915667.8257137334%2C6459688.48306598%2C918839.9623875683%2C6462793.737340063&query_layers=parkhaeuser&X=243&Y=606",
        "&bbox=915667.8257137334%2C6459688.48306598%2C918839.9623875683%2C6462793.737340063&query_layers=parkhaeuser&X=331&Y=613",
    ]

    STATUS_MAPPING = {
        "OK": LotData.Status.open,
        # TODO: After opening times lots show all numbers but this status
        #   so i guess it means "closed"
        "Nicht OK": LotData.Status.closed,
    }

    def get_lot_data(self) -> List[LotData]:
        lots = []
        for timestamp, source_url, attributes in self.iter_lot_attributes():
            lots.append(
                LotData(
                    timestamp=timestamp,
                    id=name_to_legacy_id("wiesbaden", attributes["Name"]),
                    status=self.STATUS_MAPPING.get(attributes["Status"], LotData.Status.unknown),
                    num_occupied=int_or_none(attributes["Belegt"]),
                    capacity=int_or_none(attributes["Parkplätze"]),
                )
            )

        return lots

    def iter_lot_attributes(self) -> Generator[Tuple[datetime.datetime, str, dict], None, None]:
        for url_params in self.LOT_URL_PARAMS:
            source_url = self.POOL.source_url + url_params

            timestamp = self.now()
            soup = self.request_soup(source_url, encoding="utf-8")

            attributes = {
                tr.find_all("td")[0].text.rstrip(":"): tr.find_all("td")[1].text
                for tr in soup.find_all("tr")
            }
            if attributes:
                yield timestamp, source_url, attributes

    def get_lot_infos(self) -> List[LotInfo]:
        NEW_TO_LEGACY = {
            "Mauritius Galerie": "Mauritius-Parkhaus",
            "City 1": "City I",
            "City 2": "City II",
        }
        lot_map = {
            lot.name: lot
            for lot in self.get_v1_lot_infos_from_geojson("Wiesbaden")
        }
        lots = []

        for timestamp, source_url, attributes in self.iter_lot_attributes():
            legacy_name = attributes["Name"][3:].replace("ss", "ß")
            legacy_name = NEW_TO_LEGACY.get(legacy_name, legacy_name)
            kwargs = vars(lot_map[legacy_name])
            kwargs.update(dict(
                name=attributes["Name"],
                id=name_to_legacy_id("wiesbaden", attributes["Name"]),
                has_live_capacity=True,
                source_url=source_url,
            ))
            lots.append(LotInfo(**kwargs))

        return lots
