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
        "garage": LotInfo.Types.garage,
    }

    name = name.lower()
    for key, type in NAME_TO_LOT_TYPE_MAPPING.items():
        if key in name:
            return type


def name_to_legacy_id(city_name: str, lot_name: str) -> str:
    """
    Converts city/pool name and lot name to the legacy lot ID
    identical to the original ParkAPI ID

    :param city_name: str, city or pool prefix
    :param lot_name: str, name of the lot
    :return: a normalized string
    """
    name = f"{city_name}{lot_name}".lower()
    return remove_special_chars(name)


def name_to_id(city_name: str, lot_name: str) -> str:
    """
    Converts city/pool name and lot name to a lot ID
    with only ascii characters and "-"

    :param city_name: str, city or pool prefix
    :param lot_name: str, name of the lot
    :return: a normalized string, maximum length of 64 characters!
    """
    name = f"{city_name}-{lot_name}".lower()
    return remove_special_chars_v2(name)[:64]


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
        "\t": "",
        # TODO: i added these because of lot 'karlsruhezirkel(p&c)'
        #   which is really a bad filename
        "&": "",
        "(": "",
        ")": "",
    }
    for repl in replacements.keys():
        name = name.replace(repl, replacements[repl])
    return name


def remove_special_chars_v2(name: str) -> str:
    """
    Converts any string to
      - ascii alphanumeric or "-" characters
      - no spaces
      - lowercase
    """
    replacements = {
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "ß": "ss",
    }
    id_name = str(name)
    for old, new in replacements.items():
        name = name.replace(old, new)

    id_name = id_name.replace("ß", "ss")
    id_name = unicodedata.normalize('NFKD', id_name).encode("ascii", "ignore").decode("ascii")

    id_name = "".join(
        c if c.isalnum() or c in " \t\n" else "-"
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
