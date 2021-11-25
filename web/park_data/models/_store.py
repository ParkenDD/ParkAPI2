from typing import List

from django.db import transaction
from django.contrib.gis.geos import Point

from .parking_pool import ParkingPool
from .parking_lot import ParkingLot
from .parking_data import ParkingData, ParkingLotState


def store_snapshot(snapshot: dict, update_infos: bool = True) -> List[ParkingData]:
    """
    Store a snapshot.

    :returns List of park_data.models.ParkingData instances
    """
    pool = snapshot["pool"]
    lots = snapshot["lots"]
    data_models = []

    try:
        pool_model = ParkingPool.objects.get(pool_id=pool["id"])
    except ParkingPool.DoesNotExist:
        kwargs = {key: value for key, value in pool.items() if hasattr(ParkingPool, key)}
        kwargs["pool_id"] = kwargs.pop("id")
        pool_model = ParkingPool.objects.create(**kwargs)

    for lot in lots:

        kwargs = {key: value for key, value in lot.items() if hasattr(ParkingLot, key)}
        kwargs["lot_id"] = kwargs.pop("id")
        kwargs["pool"] = pool_model
        kwargs["max_capacity"] = lot.get("capacity")
        kwargs["has_live_capacity"] = lot.get("has_live_capacity") or False
        if not (lot.get("latitude") is None or lot.get("longitude") is None):
            kwargs["geo_point"] = Point(lot["longitude"], lot["latitude"])

        try:
            lot_model = ParkingLot.objects.get(lot_id=lot["id"])

            if update_infos:
                updated = False
                for key, value in kwargs.items():
                    if value is not None and hasattr(lot_model, key) and getattr(lot_model, key) in (None, ""):
                        setattr(lot_model, key, value)
                        updated = True
                if updated:
                    lot_model.save()

        except ParkingLot.DoesNotExist:
            lot_model = ParkingLot.objects.create(**kwargs)

        kwargs = {key: value for key, value in lot.items() if hasattr(ParkingData, key)}
        kwargs.pop("id")
        kwargs["lot"] = lot_model
        data_models.append(ParkingData.objects.create(**kwargs))

    return data_models
