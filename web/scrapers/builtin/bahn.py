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
            source_url="https://api.deutschebahn.com/bahnpark/v1/spaces",
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
                self.POOL.source_url + "/occupancies",
            )

            lots = []
            for alloc in data["allocations"]:
                space, alloc = alloc["space"], alloc["allocation"]

                # --- time segment ---

                lot_timestamp = alloc.get("timeSegment")
                if lot_timestamp:
                    lot_timestamp = self.to_utc_datetime(lot_timestamp)

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

        def get_lot_infos(self) -> List[LotInfo]:
            spaces = []

            offset = 0
            while True:
                data = self.request_json(
                    self.POOL.source_url,
                    params={"offset": offset, "limit": 100}
                )
                spaces += data["items"]
                if len(spaces) >= data["totalCount"]:
                    break
                offset += len(data["items"])

            lots = []
            for space in spaces:
                # import json
                # print(json.dumps(space, indent=2)); exit()

                lots.append(
                    LotInfo(
                        id="db-%s" % space["id"],
                        name=space["name"],
                        # either street or auto-mapping
                        type=LotInfo.Types.street if space["spaceType"] == "Straße" else space["spaceType"],
                        public_url=space["url"],
                        source_url=self.POOL.source_url + "/occupancies",
                        address="\n".join(space["address"].values()),
                        capacity=int(space["numberParkingPlaces"]),
                        has_live_capacity=True,
                        latitude=space["geoLocation"]["latitude"],
                        longitude=space["geoLocation"]["longitude"],
                    )
                )

            return lots
