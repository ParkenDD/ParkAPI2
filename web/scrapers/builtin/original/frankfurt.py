"""
Original code by Romankov
"""
from typing import List

from util import *


class Frankfurt(ScraperBase):

    POOL = PoolInfo(
        id="frankfurt-main",
        name="Offene Daten Frankurt",
        public_url="https://offenedaten.frankfurt.de/dataset/parkdaten-dynamisch",
        source_url="https://offenedaten.frankfurt.de/dataset/912fe0ab-8976-4837-b591-57dbf163d6e5/resource/48378186-5732-41f3-9823-9d1938f2695e/download/parkdaten_dyn.xml",
    )

    def get_lot_data(self) -> List[LotData]:
        now = self.now()
        soup = self.request_soup(self.POOL.source_url)

        last_updated = self.to_utc_datetime(soup.find("publicationtime").text)

        lots = []

        for facility in soup.select("parkingfacilitytablestatuspublication > parkingfacilitystatus"):
            lot_id = facility.find("parkingfacilityreference")["id"]
            lot_total = int(facility.find("totalparkingcapacityshorttermoverride").text)
            # TODO: Need not find out difference between
            #   totalNumberOfOccupiedParkingSpaces and totalNumberOfVacantParkingSpaces
            #   e.g. first goes to zero or might disappear when closed while second remains
            try:
                lot_occupied = int(facility.find("totalnumberofoccupiedparkingspaces").text)
            except:
                lot_occupied = None

            state = facility.find("parkingfacilitystatus")
            if state and state.text in [LotData.Status.open, LotData.Status.closed]:
                state = state.text
            else:
                state = LotData.Status.nodata

            lots.append(
                LotData(
                    id=name_to_legacy_id("frankfurt", lot_id),
                    timestamp=now,
                    lot_timestamp=last_updated,
                    status=state,
                    num_occupied=lot_occupied,
                    capacity=lot_total,
                )
            )

        return lots

    def get_lot_infos(self) -> List[LotInfo]:
        url = "https://offenedaten.frankfurt.de/dataset/e821f156-69cf-4dd0-9ffe-13d9d6218597/resource/eac5ca3d-4285-48f4-bfe3-d3116a262e5f/download/parkdaten_sta.xml"
        soup = self.request_soup(url)

        lots = []
        for facility in soup.find_all("parkingfacility"):
            lots.append(
                LotInfo(
                    id=name_to_legacy_id("frankfurt", facility["id"]),
                    name=facility.find("parkingfacilitydescription").text,
                    type=LotInfo.Types.unknown,  # there's no data
                    source_url=self.POOL.source_url,
                    latitude=float(facility.find("pointcoordinates").find("latitude").text),
                    longitude=float(facility.find("pointcoordinates").find("longitude").text),
                    capacity=int(facility.find("totalparkingcapacity").text),
                    has_live_capacity=True,
                )
            )

        return lots
