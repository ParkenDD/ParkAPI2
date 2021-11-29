import json
from pathlib import Path
from typing import Optional

import jsonschema


def validate_snapshot(
        snapshot: dict,
        schema: Optional[dict] = None,
) -> dict:
    from .structs import LotInfo, LotData

    ret_data = {
        "errors": [],
        "warnings": [],
    }

    # --- validate schema ---

    if schema is None:
        schema = json.loads((Path(__file__).resolve().parent.parent / "schema.json").read_text())

    validator = jsonschema.Draft7Validator(schema)
    try:
        validator.validate(snapshot)
    except jsonschema.ValidationError as e:
        ret_data["errors"].append({
            "path": ".".join(str(p) for p in e.absolute_path),
            "message": e.message,
        })
        # no need to check further
        return ret_data

    if snapshot.get("error"):
        ret_data["errors"].append({
            "path": "errors",
            "message": snapshot["error"],
        })

    # --- validate "good practice" ---

    if not snapshot["pool"]["license"]:
        ret_data["warnings"].append({
            "path": "pool.license",
            "message": "Pool should have a license"
        })

    for i, lot in enumerate(snapshot["lots"]):
        if lot["type"] == LotInfo.Types.unknown:
            ret_data["warnings"].append({
                "path": f"lots.{i}.type",
                "message": f"Lot '{lot['id']}' should have a type other than 'unknown'"
            })

        for key in ("latitude", "longitude", "address", "capacity"):
            if lot[key] is None:
                ret_data["warnings"].append({
                    "path": f"lots.{i}.{key}",
                    "message": f"Lot '{lot['id']}' should have '{key}'"
                })

        if lot["num_free"] is None and lot["num_occupied"] is None:
            ret_data["warnings"].append({
                "path": f"lots.{i}.num_free",
                "message": f"Lot '{lot['id']}' should have 'num_free' or 'num_occupied'"
            })

        if lot["num_free"] is None and lot["capacity"] is None and lot["num_occupied"] is not None:
            ret_data["warnings"].append({
                "path": f"lots.{i}.capacity",
                "message": f"Lot '{lot['id']}' should have 'capacity' when defining 'num_occupied'"
            })

    return ret_data
