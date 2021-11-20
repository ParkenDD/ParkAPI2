from .city import City
from .country import Country
from .parking_data import ParkingData, ParkingLotState
from .parking_lot import ParkingLot
from .state import State


class SchemaError(Exception):
    pass


def store_lot_data(data: dict):
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

    try:
        city = City.objects.filter(name=data["city"]["name"])
    except City.DoesNotExist:
        city = City.objects.create(
            name=data["city"]["name"],
        )

    try:
        country = Country.objects.filter(code=data["country"]["code"])
    except Country.DoesNotExist:
        if not data["country"].get("name"):
            raise SchemaError("Required attribute 'country.name' missing")
        country = Country.objects.create(
            code=data["country"]["code"],
            name=data["country"].get("name"),
        )

    state = None
    if data.get("state") and data["state"].get("name"):
        try:
            state = State.objects.filter(name=data["state"]["name"])
        except State.DoesNotExist:
            state = State.objects.create(
                name=data["state"]["name"],
            )

        