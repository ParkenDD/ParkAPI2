import unittest
from copy import deepcopy
from typing import Optional

from util.validate import validate_snapshot

SNAPSHOTS = {
    "valid": {
        "pool": {
            "id": "pool-1",
            "name": "Pool 1",
            "public_url": "https://example.com",
            "timezone": "Europe/Berlin",
            "source_url": None,
            "license": "The City Of Example"
        },
        "lots": [
            {
                "id": "pool-1-lot-1",
                "name": "Lot 1",
                "type": "lot",
                "public_url": None,
                "source_url": "https://example.com/source",
                "address": "Some\nAddress",
                "capacity": 100,
                "has_live_capacity": True,
                "latitude": 50.,
                "longitude": 10.,
                "timestamp": "2021-11-29T09:10:30",
                "lot_timestamp": "2021-11-29T09:09:36",
                "status": "open",
                "num_free": 60,
                "num_occupied": 40,
            },
        ]
    },
    "warnings": {
        "pool": {
            "id": "pool-2",
            "name": "Pool 2",
            "public_url": "https://example.com",
            "timezone": "Europe/Berlin",
            "source_url": None,
            "license": None,                                # missing license
        },
        "lots": [
            {
                "id": "pool-2-lot-1",
                "name": "Lot 1",
                "type": "unknown",                          # not a good type
                "public_url": None,
                "source_url": "https://example.com/source",
                "address": None,                            # no address
                "capacity": None,                           # no capacity
                "has_live_capacity": False,
                "latitude": None,                           # no coordinates
                "longitude": None,
                "timestamp": "2021-11-29T09:10:30",
                "lot_timestamp": None,
                "status": "unknown",
                "num_free": None,                           # no data
                "num_occupied": None,
            },
        ]
    }
}


class TestValidation(unittest.TestCase):
    maxDiff = None

    def test_validation_errors(self):
        self.assertEqual(
            [{"message": "'pool' is a required property", "path": ""}],
            validate_snapshot({})["errors"]
        )

        self.assertEqual(
            [{"message": "[] is not of type 'object'", "path": "pool"}],
            validate_snapshot({
                "pool": [],
                "lots": [],
            })["errors"]
        )

        self.assertEqual(
            [{"message": "'id' is a required property", "path": "pool"}],
            validate_snapshot({
                "pool": {},
                "lots": [],
            })["errors"]
        )

        self.assertEqual(
            [],
            validate_snapshot(SNAPSHOTS["valid"])["errors"]
        )

        snapshot = deepcopy(SNAPSHOTS["valid"])
        snapshot["pool"]["id"] = "x" * 65
        self.assertEqual(
            [{"message": "'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx' is too long", "path": "pool.id"}],
            validate_snapshot(snapshot)["errors"]
        )

        snapshot = deepcopy(SNAPSHOTS["valid"])
        snapshot["lots"][0]["source_url"] = 23
        self.assertEqual(
            [{"message": "23 is not of type 'string'", "path": "lots.0.source_url"}],
            validate_snapshot(snapshot)["errors"]
        )

        snapshot = deepcopy(SNAPSHOTS["valid"])
        snapshot["pool"]["source_url"] = "www.example.com"
        self.assertEqual(
            [{"message": "'www.example.com' does not match '[a-z]+://.*'", "path": "pool.source_url"}],
            validate_snapshot(snapshot)["errors"]
        )

    def test_validation_warnings(self):
        self.assertEqual(
            [],
            validate_snapshot(SNAPSHOTS["valid"])["warnings"]
        )

        self.assertEqual(
            [
                {"message": "Pool should have a license", "path": "pool.license"},
                {"message": "Lot 'pool-2-lot-1' should have a type other than 'unknown'", "path": "lots.0.type"},
                {"message": "Lot 'pool-2-lot-1' should have 'latitude'", "path": "lots.0.latitude"},
                {"message": "Lot 'pool-2-lot-1' should have 'longitude'", "path": "lots.0.longitude"},
                {"message": "Lot 'pool-2-lot-1' should have 'address'", "path": "lots.0.address"},
                {"message": "Lot 'pool-2-lot-1' should have 'capacity'", "path": "lots.0.capacity"},
                {"message": "Lot 'pool-2-lot-1' should have 'num_free' or 'num_occupied'", "path": "lots.0.num_free"}
            ],
            validate_snapshot(SNAPSHOTS["warnings"])["warnings"]
        )

        snapshot = deepcopy(SNAPSHOTS["valid"])
        snapshot["lots"][0]["num_free"] = None
        snapshot["lots"][0]["capacity"] = None  # only specifying num_occupied

        self.assertEqual(
            [
                {"message": "Lot 'pool-1-lot-1' should have 'capacity'", "path": "lots.0.capacity"},
                {"message": "Lot 'pool-1-lot-1' should have 'capacity' when defining 'num_occupied'", "path": "lots.0.capacity"}
            ],
            validate_snapshot(snapshot)["warnings"]
        )
