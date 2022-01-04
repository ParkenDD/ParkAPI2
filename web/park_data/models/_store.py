from typing import List, Optional

from django.db import transaction
from django.contrib.gis.geos import Point

from .parking_pool import ParkingPool
from .parking_lot import ParkingLot
from .parking_data import ParkingData, LatestParkingData


def store_snapshot(
        snapshot: dict,
        update_infos: bool = True,
) -> List[ParkingData]:
    """
    Store a snapshot.

    :param update_infos: bool, Update any fields of ParkingPool and ParkingLot
        if meta-information changed

    :returns List of park_data.models.ParkingData instances
    """
    pool = snapshot["pool"]
    lots = snapshot["lots"]
    data_models = []

    kwargs = {key: value for key, value in pool.items() if hasattr(ParkingPool, key)}
    kwargs["pool_id"] = kwargs.pop("id")
    try:
        pool_model = ParkingPool.objects.get(pool_id=pool["id"])

        if update_infos:
            updated = False
            for key, value in kwargs.items():
                if value is not None and hasattr(pool_model, key) and getattr(pool_model, key) != value:
                    setattr(pool_model, key, value)
                    updated = True
            if updated:
                pool_model.save()

    except ParkingPool.DoesNotExist:
        pool_model = ParkingPool.objects.create(**kwargs)

    for lot in lots:

        kwargs = {key: value for key, value in lot.items() if hasattr(ParkingLot, key)}
        kwargs["lot_id"] = kwargs.pop("id")
        kwargs["pool"] = pool_model
        kwargs["max_capacity"] = max_or_none(lot.get("capacity"), lot.get("num_free"))
        kwargs["has_live_capacity"] = lot.get("has_live_capacity") or False
        if not (lot.get("latitude") is None or lot.get("longitude") is None):
            kwargs["geo_point"] = Point(lot["longitude"], lot["latitude"])

        try:
            lot_model = ParkingLot.objects.get(lot_id=lot["id"])

            updated = False
            max_capacity = max_or_none(kwargs["max_capacity"], lot_model.max_capacity)
            if max_capacity != lot_model.max_capacity:
                lot_model.max_capacity = max_capacity
                updated = True

            if update_infos:
                kwargs.pop("max_capacity")
                for key, value in kwargs.items():
                    if value is not None and hasattr(lot_model, key) and getattr(lot_model, key) != value:
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

        # --- update LatestParkingData ---

        kwargs.pop("lot")
        if not lot_model.latest_data:
            lot_model.latest_data = LatestParkingData.objects.create(**kwargs)
            lot_model.save()
        else:
            updated = False
            for key, value in kwargs.items():
                if value != getattr(lot_model.latest_data, key):
                    setattr(lot_model.latest_data, key, value)
                    updated = True
            if updated:
                lot_model.latest_data.save()

    return data_models


def max_or_none(a: Optional[int], b: Optional[int]) -> Optional[int]:
    if a is None:
        if b is None:
            return None
        return b
    elif b is None:
        return a
    return max(a, b)
