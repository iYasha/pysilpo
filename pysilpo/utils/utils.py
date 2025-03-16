import logging
from datetime import datetime

import jwt


def get_logger(name: str = "PySilpo") -> logging.Logger:
    return logging.getLogger(name)


def get_jwt_expires_in(jwt_token: str) -> int:
    decoded = jwt.decode(jwt_token, options={"verify_signature": False})
    return decoded["exp"]


def subtract_months(date: datetime, months: int) -> datetime:
    """
    Subtract a specified number of months from a datetime object.

    Args:
        date: A datetime object to subtract months from
        months: Number of months to subtract (positive integer)

    Returns:
        A new datetime object with the months subtracted
    """
    if months < 0:
        raise ValueError("months should be a positive integer")

    year = date.year
    month = date.month

    month -= months

    while month <= 0:
        year -= 1
        month += 12

    if date.day > 28:
        if month == 2:
            last_day = 29 if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0) else 28
        elif month in [4, 6, 9, 11]:
            last_day = 30
        else:
            last_day = 31

        new_day = min(date.day, last_day)
    else:
        new_day = date.day

    return datetime(
        year=year,
        month=month,
        day=new_day,
        hour=date.hour,
        minute=date.minute,
        second=date.second,
        microsecond=date.microsecond,
        tzinfo=date.tzinfo,
    )
