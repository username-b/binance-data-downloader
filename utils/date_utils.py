from datetime import date, timedelta, datetime
from typing import Iterator


def _to_date(d: date | str) -> date:
    if isinstance(d, date):
        return d
    return datetime.fromisoformat(d).date()


def daterange(
    start_date: date | str,
    end_date: date | str,
) -> Iterator[date]:
    """
    Генератор дат [start_date, end_date] включительно.
    Поддерживает date и ISO-строки.
    """

    start = _to_date(start_date)
    end = _to_date(end_date)

    if start > end:
        raise ValueError("start_date must be <= end_date")

    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)
