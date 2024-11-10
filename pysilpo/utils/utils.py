import logging
from datetime import datetime, timedelta

import jwt


def get_logger(name: str = "PySilpo") -> logging.Logger:
    return logging.getLogger(name)


def get_jwt_expires_in(jwt_token: str) -> int:
    decoded = jwt.decode(jwt_token, options={"verify_signature": False})
    return decoded["exp"]


def subtract_months(date: datetime, months: int) -> datetime:
    # Calculate target year and month
    target_month = date.month - months
    target_year = date.year + (target_month - 1) // 12  # Adjust year if month < 1
    target_month = (target_month - 1) % 12 + 1  # Adjust month to range 1-12

    # Calculate last day of the target month
    last_day_of_month = (datetime(target_year, target_month + 1, 1) - timedelta(days=1)).day
    target_day = min(date.day, last_day_of_month)  # Ensure valid day of month

    # Return new date with adjusted year, month, and day
    return datetime(target_year, target_month, target_day, date.hour, date.minute, date.second)
