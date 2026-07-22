import random
from datetime import datetime, timedelta, date


def generate_schedule(
    end_date: datetime,
    count: int,
    start_date: date = None,
    shuffle: bool = False,
    _now: datetime = None,
) -> list:
    """
    Distributes `count` pins evenly across range_start → range_end.

    range_start logic:
    - start_date tidak diisi atau start_date == hari ini → now + 2 jam
    - start_date == besok atau lebih → tengah malam hari itu + 2 jam (02:00)

    range_end = end_date 23:59:59

    interval = total_seconds / count, rounded to nearest minute.

    shuffle=True  → slot diacak urutannya.
    shuffle=False → slot urut kronologis (default).
    """
    now = _now or datetime.now()
    today = now.date()

    if start_date is None or start_date <= today:
        # Hari ini: mulai dari now + 2 jam
        range_start = now.replace(second=0, microsecond=0) + timedelta(hours=2)
    else:
        # Besok atau lebih: mulai dari tengah malam + 2 jam = 02:00
        range_start = datetime(start_date.year, start_date.month, start_date.day, 2, 0, 0)

    range_end = datetime(
        end_date.year, end_date.month, end_date.day,
        23, 59, 59
    ) if isinstance(end_date, date) and not isinstance(end_date, datetime) else \
        end_date.replace(hour=23, minute=59, second=59, microsecond=0)

    if range_start >= range_end:
        raise ValueError(f"range_start ({range_start}) must be before range_end ({range_end})")
    if count <= 0:
        raise ValueError("count must be a positive integer")

    total_seconds    = (range_end - range_start).total_seconds()
    interval_sec     = total_seconds / count
    interval_rounded = max(60, round(interval_sec / 60) * 60)

    slots = []
    for i in range(count):
        candidate = range_start + timedelta(seconds=i * interval_rounded)
        candidate = candidate.replace(second=0, microsecond=0)
        slots.append(candidate)

    if shuffle:
        random.shuffle(slots)

    return [dt.strftime("%Y-%m-%dT%H:%M:%S") for dt in slots]


if __name__ == "__main__":
    from pprint import pprint

    fake_now = datetime(2025, 1, 1, 10, 0, 0)  # jam 10 pagi

    print("=== start_date = hari ini (now+2h) ===")
    pprint(generate_schedule(datetime(2025, 1, 3), count=5, start_date=date(2025, 1, 1), _now=fake_now))

    print("\n=== start_date = besok (02:00) ===")
    pprint(generate_schedule(datetime(2025, 1, 3), count=5, start_date=date(2025, 1, 2), _now=fake_now))

    print("\n=== tanpa start_date (default now+2h) ===")
    pprint(generate_schedule(datetime(2025, 1, 3), count=5, _now=fake_now))
