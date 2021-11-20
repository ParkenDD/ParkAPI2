from typing import List

from django.db import transaction

from .city import City
from .country import Country
from .parking_data import ParkingData, ParkingLotState
from .parking_lot import ParkingLot
from .state import State


class SchemaError(Exception):
    pass


def store_lot_data(data: dict) -> List[ParkingData]:
    """

    :param data:

        (R) means 'required'

        {
            "timestamp": str|datetime,      # (R) timestamp of snapshot
            "city": {
                "name": str (64),           # (R)
            },
            "state": {                      # optional
                "name": str (64),
            },
            "country": {                    # (R)
                "code": str (2),            # two-letter ISO 3166 country code
                "name": str (64),           # name is optional if country is already known
            },
            "lots": [                       # (R)
                {
                    "id": str (64),         # (R) unique persistent ID of parking lot
                    "status": str (16),     # (R) see park_data.models.parking_data.ParkingLotStates

                    # below are all optional

                    "num_free": int,
                    "num_total": int,
                    "num_occupied": int,

                    "name": str (64),       # only required if 'id' is unknown
                    "address": str (1024),
                }
            ]
        }

    :return: list of saved instances of park_data.models.ParkingData
    """
    if not data.get("timestamp"):
        raise SchemaError("Required attribute 'timestamp' missing")

    if not data.get("city") or not data["city"].get("name"):
        raise SchemaError("Required attribute 'city.name' missing")

    if not data.get("country") or not data["country"].get("code"):
        raise SchemaError("Required attribute 'country.code' missing")

    if "lots" not in data:
        raise SchemaError("Required attribute 'lots' missing")

    # put everything into a transaction so that further validation
    #    errors leave the database unchanged
    with transaction.atomic():

        try:
            country = Country.objects.get(iso_code=data["country"]["code"])
        except Country.DoesNotExist:
            if not data["country"].get("name"):
                raise SchemaError("Required attribute 'country.name' missing")
            country = Country.objects.create(
                iso_code=data["country"]["code"],
                name=data["country"].get("name"),
            )

        state = None
        if data.get("state") and data["state"].get("name"):
            try:
                state = State.objects.get(name=data["state"]["name"])
            except State.DoesNotExist:
                state = State.objects.create(
                    name=data["state"]["name"],
                    country=country,
                )

        try:
            city = City.objects.get(name=data["city"]["name"])
        except City.DoesNotExist:
            city = City.objects.create(
                name=data["city"]["name"],
                state=state,
                country=country,
            )

        # --- get all ParkingLot instances ---

        lot_mapping = dict()

        for i, lot_data in enumerate(data["lots"]):
            if not lot_data.get("id"):
                raise SchemaError(f"Required attribute 'lots.{i}.id' missing")
            if not lot_data.get("status"):
                raise SchemaError(f"Required attribute 'lots.{i}.status' missing")

            if lot_data["id"] in lot_mapping:
                continue

            try:
                lot_model = ParkingLot.objects.get(lot_id=lot_data["id"])
            except ParkingLot.DoesNotExist:
                if not lot_data.get("name"):
                    raise SchemaError(f"Required attribute 'lots.{i}.name' missing")
                lot_model = ParkingLot.objects.create(
                    lot_id=lot_data["id"],
                    name=lot_data["name"],
                    address=lot_data.get("address"),
                    city=city,
                )

            lot_mapping[lot_data["id"]] = lot_model

        # --- store ParkingData instances ---

        parking_data_models = []

        for i, lot_data in enumerate(data["lots"]):
            num_free = lot_data.get("num_free")
            num_total = lot_data.get("num_total")
            num_occupied = lot_data.get("num_occupied")
            percent_free = None

            if num_free is not None:
                if num_total is not None:
                    if num_occupied is None:
                        num_occupied = num_total - num_free
                    else:
                        if num_occupied != num_total - num_free:
                            raise SchemaError(
                                f"Invalid 'lots.{i}.num_occuppied', "
                                f"got free={num_free}, total={num_total}, occupied={num_occupied}"
                            )
                    percent_free = num_free * 100 / num_total

            parking_data_models.append(
                ParkingData(
                    timestamp=data["timestamp"],
                    lot=lot_mapping[lot_data["id"]],
                    status=lot_data["status"],
                    num_free=num_free,
                    num_total=num_total,
                    num_occupied=num_occupied,
                    percent_free=percent_free,
                )
            )

        return ParkingData.objects.bulk_create(parking_data_models)