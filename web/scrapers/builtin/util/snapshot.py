import datetime
import traceback

from .scraper import ScraperBase
from .structs import LotInfo, LotData, PoolInfo


class SnapshotMaker:

    def __init__(self, scraper: ScraperBase):
        self.scraper = scraper

    def info_map_to_geojson(
            self,
            include_unknown: bool = False,
            include_all_infos: bool = False,
    ) -> dict:
        """
        Convert the Scraper.get_lot_infos() result to geojson.

        :param include_unknown:
            if True, id's that are in get_lot_data but not in
            get_lot_infos will be initialized with default values

        :param include_all_infos:
            if True, all lots from get_lot_infos will be converted
            to geojson, even if they are not in get_lot_data

        :return: geojson dict
        """
        info_map = self.scraper.get_lot_info_map(required=not include_unknown)

        if include_unknown or not include_all_infos:
            lot_data_list = self.scraper.get_lot_data()
            lot_data_map = {lot_data.id: lot_data for lot_data in lot_data_list}

            if include_unknown:
                for lot in lot_data_list:
                    if lot.id not in info_map:
                        # create a minimal lot info
                        info_map[lot.id] = LotInfo(
                            id=lot.id, name=lot.id, type=LotInfo.Types.lot,
                        )

            if not include_all_infos:
                info_map = {key: value for key, value in info_map.items() if key in lot_data_map}

        ret_data = {
            "type": "FeatureCollection",
            "features": []
        }
        for info in info_map.values():
            info = vars(info).copy()
            lat, lon = info.pop("latitude", None), info.pop("longitude", None)
            feature = {
                "type": "Feature",
                "properties": info,
            }
            if not (lat is None or lon is None):
                feature["geometry"] = {
                    "type": "Point",
                    "coordinates": [lon, lat]
                }
            ret_data["features"].append(feature)

        ret_data["features"].sort(key=lambda f: f["properties"]["id"])
        return ret_data

    def get_snapshot(self, infos_required: bool = True) -> dict:
        snapshot = {
            "pool": vars(self.scraper.POOL),
            "lots": [],
        }
        try:
            info_map = self.scraper.get_lot_info_map(required=infos_required)

            lot_id_set = set()
            for lot_data in self.scraper.get_lot_data():
                if lot_data.id in lot_id_set:
                    raise ValueError(
                        f"Duplicate LotData id '{lot_data.id}' in {lot_data}"
                    )
                lot_id_set.add(lot_data.id)

                if lot_data.id in info_map:
                    merged_lot = vars(info_map[lot_data.id])
                else:
                    if infos_required:
                        raise ValueError(
                            f"Lot {lot_data.id} is not in lot_infos"
                        )
                    merged_lot = dict()

                for key, value in vars(lot_data).items():
                    if key not in merged_lot or value is not None:
                        merged_lot[key] = value

                for key, value in merged_lot.items():
                    if isinstance(value, datetime.datetime):
                        merged_lot[key] = value.isoformat()

                snapshot["lots"].append(merged_lot)

        except Exception as e:
            snapshot["error"] = f"""{type(e).__name__}: {e}\n{traceback.format_exc()}"""
        return snapshot
