import datetime
from typing import Optional

import dateutil.parser
import pytz


def to_utc_datetime(
        date_string: str,
        date_format: Optional[str] = None,
        timezone: Optional[str] = None,
) -> datetime.datetime:
    """
    Convert a date string into a UTC datetime.

    Will always raise ValueError if parsing fails.

    :param date_string: str, The date string
    :param date_format: str|None, Optional format for parsing the date string
    :param timezone: str|None, the timezone of the parsed date, defaults to UTC

    :return: datetime, in UTC but without tzinfo
    """
    try:
        if date_format:
            dt = datetime.datetime.strptime(date_string, date_format)
        else:
            dt = dateutil.parser.parse(date_string)
    except Exception as e:
        raise ValueError(f"Can not parse date '{date_string}': {e}")

    if timezone is not None:
        local_timezone = pytz.timezone(timezone)

        if dt.tzinfo:
            pass  # we just convert from that timezone to UTC
        else:
            dt = local_timezone.localize(dt, is_dst=None)

    if dt.tzinfo:
        dt = dt.astimezone(pytz.utc).replace(tzinfo=None)

    return dt.replace(microsecond=0)
