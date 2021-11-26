import re
import unicodedata
from typing import Union, Optional, Tuple, List, Type, Dict


RE_MULTI_MINUS = re.compile(r"--+")


def guess_lot_type(name: str) -> Optional[str]:
    from .structs import LotInfo

    NAME_TO_LOT_TYPE_MAPPING = {
        "parkplatz": LotInfo.Types.lot,
        "parkplätze": LotInfo.Types.lot,
        "parkhaus": LotInfo.Types.garage,
        "parkgarage": LotInfo.Types.garage,
        "tiefgarage": LotInfo.Types.underground,
        "parkdeck": LotInfo.Types.level,
        "parklevel": LotInfo.Types.level,
    }

    name = name.lower()
    for key, type in NAME_TO_LOT_TYPE_MAPPING.items():
        if key in name:
            return type


def remove_special_chars(name: str) -> str:
    """
    Remove any umlauts, spaces and punctuation from a string.
    """
    replacements = {
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "ß": "ss",
        "-": "",
        " ": "",
        ".": "",
        ",": "",
        "'": "",
        "\"": "",
        "/": "",
        "\\": "",
        "\n": "",
        "\t": ""
    }
    for repl in replacements.keys():
        name = name.replace(repl, replacements[repl])
    return name


def name_to_id(name: str) -> str:
    """
    Converts any string to
      - ascii alphanumeric or "-" characters
      - no spaces
      - lowercase
      - maximal length of 64
    """
    id_name = str(name)
    id_name = id_name.replace("ß", "ss")
    id_name = unicodedata.normalize('NFKD', id_name).encode("ascii", "ignore").decode("ascii")

    id_name = "".join(
        c if c.isalnum() or c in " \t" else "-"
        for c in id_name
    ).replace(" ", "-")

    id_name = RE_MULTI_MINUS.sub("-", id_name).strip("-")
    return id_name.lower()[:64]


def int_or_none(x) -> Optional[int]:
    try:
        x = str(x)
        if len(x) > 1:
            x = x.lstrip("0")
        return int(x)
    except (ValueError, TypeError):
        return None


def float_or_none(x) -> Optional[float]:
    try:
        return float(str(x))
    except (ValueError, TypeError):
        return None
