import os
import warnings
from typing import List

from util import *

BAHN_API_TOKEN = os.environ.get("BAHN_API_TOKEN")

if not BAHN_API_TOKEN:
    warnings.warn("Deutsche Bahn Parking API disabled! You need to define BAHN_API_TOKEN in environment")

else:

    class BahnParking(ScraperBase):

        POOL = PoolInfo(
            id="bahn",
            name="Deutsche Bahn Parkplätze API",
            public_url="https://data.deutschebahn.com/dataset/api-parkplatz.html",
            source_url="https://api.deutschebahn.com/bahnpark/v1/spaces/occupancies",
            license="Creative Commons Attribution 4.0 International (CC BY 4.0)",
            timezone="Europe/Berlin",  # i guess
        )

        HEADERS = {
            "Authorization": f"Bearer {BAHN_API_TOKEN}"
        }

        # TODO: This is really not translatable to numbers
        #   that are meaningful in all cases..
        ALLOCATION_TEXT_TO_NUM_FREE_MAPPING = {
            "bis 10": 5,
            "> 10": 11,
            "> 30": 31,
            "> 50": 51,
        }

        def get_lot_data(self) -> List[LotData]:
            now = self.now()
            data = self.request_json(
                self.POOL.source_url,
            )
            import json
            print(json.dumps(data, indent=2))

            lots = []
            for alloc in data["allocations"]:
                space, alloc = alloc["space"], alloc["allocation"]

                # --- time segment ---

                lot_timestamp = alloc.get("timeSegment")
                if lot_timestamp:
                    lot_timestamp = self.convert_date(lot_timestamp)

                # --- status ---

                status = LotData.Status.nodata
                if alloc.get("validData"):
                    status = LotData.Status.open

                # --- num free ---

                num_free_text = alloc.get("text")
                num_free = None

                if not num_free_text:
                    if status == LotData.Status.open:
                        status = LotData.Status.error
                else:
                    num_free = self.ALLOCATION_TEXT_TO_NUM_FREE_MAPPING[num_free_text]

                lots.append(
                    LotData(
                        id="db-%s" % space["id"],
                        timestamp=now,
                        lot_timestamp=lot_timestamp,
                        status=status,
                        num_free=num_free,
                        capacity=alloc.get("capacity"),
                    )
                )

            return lots

        def XX_get_lot_infos(self) -> List[LotInfo]:
            soup = self.request_soup(url)

            lots = []
            for facility in soup.find_all("parkingfacility"):
                lots.append(
                    LotInfo(
                        id=f"fam-{facility['id']}",
                        name=facility.find("parkingfacilitydescription").text,
                        type="lot",  # there's no data
                        source_url=self.POOL.source_url,
                        latitude=float(facility.find("pointcoordinates").find("latitude").text),
                        longitude=float(facility.find("pointcoordinates").find("longitude").text),
                        capacity=int(facility.find("totalparkingcapacity").text),
                        has_live_capacity=True,
                    )
                )

            return lots