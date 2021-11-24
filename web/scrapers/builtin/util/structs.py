import datetime
from typing import Union, Optional, Tuple, List, Type, Dict

from .strings import name_to_id


class PoolInfo:

    def __init__(
            self,
            id: str,
            name: str,
            web_url: str,
            timezone: str = "Europe/Berlin",
            source_url: Optional[str] = None,
            license: Optional[str] = None,
    ):
        self.id = name_to_id(id)
        self.name = name
        self.web_url = web_url
        self.timezone = timezone
        self.source_url = source_url or None
        self.license = license or None


class LotInfo:

    def __init__(
            self,
            id: str,
            name: str,
            type: Optional[str] = None,
            web_url: Optional[str] = None,
            source_url: Optional[str] = None,
            address: Optional[str] = None,
            capacity: Optional[int] = None,
            has_live_capacity: bool = False,
            latitude: Optional[float] = None,
            longitude: Optional[float] = None,
    ):
        self.id = name_to_id(id)
        self.name = name
        self.type = type
        self.web_url = web_url or None
        self.source_url = source_url or None
        self.address = address or None
        self.capacity = capacity
        self.has_live_capacity = has_live_capacity
        self.latitude = latitude
        self.longitude = longitude

        if self.type is None:
            name = self.name.lower()
            if "parkplatz" in name:
                self.type = "lot"
            elif "parkhaus" in name:
                self.type = "garage"
            elif "tiefgarage" in name:
                self.type = "underground"
            elif "parkdeck" in name:
                self.type = "level"
            else:
                raise ValueError(
                    f"Can not guess the type of lot '{self.name}', please specify with 'type'"
                )

    @classmethod
    def from_dict(cls, data: dict) -> "LotInfo":
        kwargs = {
            key: data[key]
            for key in [
                "id", "name", "type", "web_url", "source_url", "address",
                "capacity", "has_live_capacity",
                "latitude", "longitude",
            ]
            if key in data
        }
        return cls(**kwargs)


class LotData:

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
