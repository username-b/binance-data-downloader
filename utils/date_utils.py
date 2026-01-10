from datetime import date, timedelta
from typing import Iterator


def daterange(
    start_date: date,
    end_date: date,
) -> Iterator[date]:
    """
    Генератор дат [start_date, end_date] включительно.

    Пример:
    --------
    for day in daterange(date(2021, 1, 1), date(2021, 1, 3)):
        print(day)

    2021-01-01
    2021-01-02
    2021-01-03
    """

    if start_date > end_date:
        raise ValueError("start_date must be <= end_date")

    current = start_date

    while current <= end_date:
        yield current
        current += timedelta(days=1)
