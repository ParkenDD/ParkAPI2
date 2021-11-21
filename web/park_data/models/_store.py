from typing import List

from django.db import transaction

from .city import City
from .country import Country
from .parking_data import ParkingData, ParkingLotState
from .parking_lot import ParkingLot
from .state import State


class SchemaError(Exception):
    pass


def store_location_data(data: dict) -> List[ParkingLot]:
    """
    Store a couple of ParkingLot models.

    Each ParkingLot has a unique ID and must be associated to a City.

    City, State and Country models are uniquely identified by OpenStreetMap IDs.

    :param data:

        A dict looking like:

            (R) is required
            ( ) is optional

            {
                "lots": [
                    {
                        "id": str (64),                 # (R) unique persistent ID of parking lot
                                                        #   typically: "city_street-name" or "city_ID" if
                                                        #   a persistent ID is known.
                        "name": str (64),               # ( ) name of the parking lot
                        "osm_id": int,                  # ( ) OpenStreetMap ID if available
                        "city_osm_id": int,             # (R) OSM ID of city
                        "state_osm_id": int,            # ( ) OSM ID of (federal) state
                        "country_osm_id": int,          # ( ) OSM ID of country
                        "country_code": str (2),        # ( ) two-letter ISO 3166 country code (will be lower-cased)
                                                        #   required if 'county_osm_id' is new

                        "address": str (1024),          # ( ) free text address
                        "lot_type": str (64),           # ( ) type (no naming convention yet but probably burns down to:
                                                        #       street, garage, underground)
                        "public_url": str (4096),       # ( ) an informational website
                    }
                ]
            }

        The lot `id` must not repeat in the list.

    :returns List of park_data.models.ParkingLot instances
    """
    if "lots" not in data:
        raise SchemaError("Required attribute 'lots' missing")

    country_mapping = dict()
    state_mapping = dict()
    city_mapping = dict()
    lot_set = set()
    lot_models = []

    # put everything into a transaction so that further validation
    #    errors leave the database unchanged
    with transaction.atomic():

        for i, lot in enumerate(data["lots"]):
            if not lot.get("id"):
                raise SchemaError(f"Required attribute 'lots.{i}.id' missing")
            if not lot.get("city_osm_id"):
                raise SchemaError(f"Required attribute 'lots.{i}.city_osm_id' missing")

            if lot.get("country_osm_id") and lot["country_osm_id"] not in country_mapping:
                try:
                    country = Country.objects.get(osm_id=lot["country_osm_id"])
                except Country.DoesNotExist:
                    if not lot.get("country_code"):
                        raise SchemaError(f"Required attribute 'lots.{i}.country_code' missing")

                    country = Country.objects.create(
                        osm_id=lot["country_osm_id"],
                        iso_code=lot["country_code"].lower(),
                    )
                country_mapping[lot["country_osm_id"]] = country

            if lot.get("state_osm_id") and lot["state_osm_id"] not in state_mapping:
                try:
                    state = State.objects.get(osm_id=lot["state_osm_id"])
                except State.DoesNotExist:
                    state = State.objects.create(
                        osm_id=lot["state_osm_id"],
                        country=country_mapping[lot["country_osm_id"]],
                    )
                state_mapping[lot["state_osm_id"]] = state

            if lot["city_osm_id"] not in city_mapping:
                try:
                    city = City.objects.get(osm_id=lot["city_osm_id"])
                except City.DoesNotExist:
                    city = City.objects.create(
                        osm_id=lot["city_osm_id"],
                        country=country_mapping.get(lot.get("country_osm_id")),
                        state=state_mapping[lot["state_osm_id"]] if lot.get("state_osm_id") else None,
                    )
                city_mapping[lot["city_osm_id"]] = city

            if lot["id"] in lot_set:
                raise SchemaError(f"Duplicate lot id '{lot['id']}' in 'lots.{i}.id'")

            try:
                lot_model = ParkingLot.objects.get(lot_id=lot["id"])
            except ParkingLot.DoesNotExist:
                lot_model = ParkingLot.objects.create(
                    lot_id=lot["id"],
                    city=city_mapping[lot["city_osm_id"]],
                    name=lot.get("name") or None,
                    address=lot.get("address") or None,
                )
            lot_set.add(lot["id"])
            lot_models.append(lot_model)

    return lot_models


def store_lot_data(data: dict) -> List[ParkingData]:
    """
    Store the scraped parking lot data for a couple of lots.

    Each ParkingLot must be created previously.

    :param data:

        A dict with the following layout:

            (R) means 'required'

            {
                "timestamp": str|datetime,      # (R) timestamp of snapshot
                "lots": [                       # (R)
                    {
                        "id": str (64),         # (R) unique persistent ID of parking lot
                        "status": str (16),     # (R) see park_data.models.parking_data.ParkingLotStates

                        "num_free": int,        # supply any of these numbers if available
                        "num_total": int,
                        "num_occupied": int,
                    }
                ]
            }

        The lot `id` must not repeat in the list and generally there
        can only be **one** entry per timestamp/lot_id combination.

    :return: list of saved instances of park_data.models.ParkingData
    """
    if not data.get("timestamp"):
        raise SchemaError("Required attribute 'timestamp' missing")

    if "lots" not in data:
        raise SchemaError("Required attribute 'lots' missing")

    # put everything into a transaction so that further validation
    #    errors leave the database unchanged
    with transaction.atomic():

        # --- get all ParkingLot instances ---

        lot_mapping = dict()

        for i, lot_data in enumerate(data["lots"]):
            if not lot_data.get("id"):
                raise SchemaError(f"Required attribute 'lots.{i}.id' missing")
            if not lot_data.get("status"):
                raise SchemaError(f"Required attribute 'lots.{i}.status' missing")

            if lot_data["id"] not in lot_mapping:
                try:
                    lot_model = ParkingLot.objects.get(lot_id=lot_data["id"])
                except ParkingLot.DoesNotExist:
                    raise SchemaError(f"'lots.{i}.id' '{lot_data['id']}' is unknown")

            lot_mapping[lot_data["id"]] = lot_model

        # --- store ParkingData instances ---

        parking_data_models = []
        update_max_num_total = []

        for i, lot_data in enumerate(data["lots"]):
            num_free = lot_data.get("num_free")
            num_total = lot_data.get("num_total")
            num_occupied = lot_data.get("num_occupied")
            percent_free = None

            # validate and potentially complete the num_xxx values
            if num_free is not None:
                if num_total is not None:
                    if num_occupied is None:
                        num_occupied = num_total - num_free
                    else:
                        if num_occupied != num_total - num_free:
                            raise SchemaError(
                                f"Invalid 'lots.{i}.num_occupied', "
                                f"got free={num_free}, total={num_total}, occupied={num_occupied}"
                            )
                    percent_free = num_free * 100 / num_total

            lot_model = lot_mapping[lot_data["id"]]

            parking_data_models.append(
                ParkingData(
                    timestamp=data["timestamp"],
                    lot=lot_model,
                    status=lot_data["status"],
                    num_free=num_free,
                    num_total=num_total,
                    num_occupied=num_occupied,
                    percent_free=percent_free,
                )
            )

            if num_total is not None:
                if lot_model.max_num_total is None or num_total > lot_model.max_num_total:
                    lot_model.max_num_total = num_total
                    update_max_num_total.append(lot_model)

        if update_max_num_total:
            ParkingLot.objects.bulk_update(update_max_num_total, ["max_num_total"])

        return ParkingData.objects.bulk_create(parking_data_models)
