import datetime
from typing import Union, Optional, Tuple, List, Type, Dict

from .strings import name_to_id, guess_lot_type


class Struct:
    def __repr__(self):
        return f"{self.__class__.__name__}(%s)" % (
            ", ".join(
                f"{key}={repr(value)}"
                for key, value in vars(self).items()
            )
        )


class PoolInfo(Struct):

    def __init__(
            self,
            id: str,
            name: str,
            public_url: str,
            timezone: str = "Europe/Berlin",
            source_url: Optional[str] = None,
            license: Optional[str] = None,
    ):
        self.id = name_to_id(id)
        self.name = name
        self.public_url = public_url
        self.timezone = timezone
        self.source_url = source_url or None
        self.license = license or None


class LotInfo(Struct):

    class Types:
        bus = "bus"
        garage = "garage"
        level = "level"
        lot = "lot"                     # default type if nothing else fits
        street = "street"
        underground = "underground"
        unknown = "unknown"             # A bad type, but better than saying something that might be wrong

    def __init__(
            self,
            id: str,
            name: str,
            type: Optional[str] = None,
            public_url: Optional[str] = None,
            source_url: Optional[str] = None,
            address: Optional[str] = None,
            capacity: Optional[int] = None,
            has_live_capacity: bool = False,
            latitude: Optional[Union[str, float]] = None,
            longitude: Optional[Union[str, float]] = None,
    ):
        self.id = name_to_id(id)
        self.name = name
        self.type = type
        self.public_url = public_url or None
        self.source_url = source_url
        self.address = address or None
        self.capacity = capacity
        self.has_live_capacity = has_live_capacity
        self.latitude = latitude
        self.longitude = longitude

        if self.type is None:
            self.type = guess_lot_type(self.name)
            if self.type is None:
                raise ValueError(
                    f"Can not guess the type of lot '{self.name}', please specify with 'type'"
                )
        else:
            if self.type not in vars(LotInfo.Types):
                guessed_type = guess_lot_type(self.type)
                if guessed_type:
                    self.type = guessed_type
                else:
                    raise ValueError(
                        f"Lot type '{self.type}' is invalid, please use one of %s" % (
                            ", ".join(filter(lambda n: not n.startswith("_"), vars(LotInfo.Types)))
                        )
                    )

        for key in ("latitude", "longitude"):
            value = getattr(self, key)
            if value is not None:
                try:
                    value = float(value)
                except (ValueError, TypeError) as e:
                    raise ValueError(
                        f"LotInfo '{self.name}' got invalid {key} '{value}'"
                    )
                setattr(self, key, value)
                if not (-180 <= value <= 180):
                    raise ValueError(
                        f"LotInfo '{self.name}', {key} '{value}' out of bounds"
                    )

    @classmethod
    def from_dict(cls, data: dict) -> "LotInfo":
        dummy = cls(id="id", name="name", type=LotInfo.Types.unknown, source_url="https://")
        keys = list(vars(dummy))
        kwargs = {
            key: data[key]
            for key in keys
            if key in data
        }
        return cls(**kwargs)


class LotData(Struct):

    class Status:
        open = "open"           # it's listed as open
        closed = "closed"       # it's listed as closed
        unknown = "unknown"     # status is not listed
        nodata = "nodata"       # whether num_free or num_occupied is not listed
        error = "error"         # http connection error or similar

    def __init__(
            self,
            timestamp: datetime.datetime,
            id: str,
            status: str,
            num_free: Optional[int] = None,
            num_occupied: Optional[int] = None,
            capacity: Optional[int] = None,
            lot_timestamp: Optional[datetime.datetime] = None
    ):
        self.id = name_to_id(id)
        self.timestamp = timestamp
        self.status = status
        self.num_free = num_free
        self.num_occupied = num_occupied
        self.capacity = capacity
        self.lot_timestamp = lot_timestamp

        validate_timestamp(self.timestamp, f"data {self.id}")
        if self.lot_timestamp is not None:
            validate_timestamp(self.lot_timestamp, f"data {self.id}")

        if self.status.startswith("_") or status not in vars(self.Status):
            raise ValueError(
                f"Lot '{self.id}' status must be one of %s" % (
                    ", ".join(key for key in vars(self.Status) if not key.startswith("_"))
                )
            )

        if self.capacity is not None:

            if self.num_free is not None:
                if self.num_occupied is None:
                    self.num_occupied = self.capacity - self.num_free
                else:
                    if self.num_occupied != self.capacity - self.num_free:
                        raise ValueError(
                            f"Lot '{self.id}' has invalid 'num_occupied' {self.num_occupied}"
                            f", expected {self.capacity - self.num_free}"
                            f" (free={self.num_free}, capacity={self.capacity})"
                        )

            elif self.num_occupied is not None:
                if self.num_free is None:
                    self.num_free = self.capacity - self.num_occupied
                else:
                    if self.num_free != self.capacity - self.num_occupied:
                        raise ValueError(
                            f"Lot '{self.id}' has invalid 'num_free' {self.num_free}"
                            f", expected {self.capacity - self.num_occupied}"
                            f" (occupied={self.num_occupied}, capacity={self.capacity})"
                        )


def validate_timestamp(timestamp: datetime.datetime, parent: str):

    if not isinstance(timestamp, datetime.datetime):
        raise ValueError(
            f"'{parent}'.timestamp must datetime, got '{type(timestamp).__name__}'"
        )

    if timestamp.tzinfo:
        raise ValueError(
            f"'{parent}'.timestamp must be UTC and not contain a tzinfo"
            f", got '{timestamp}'"
        )
