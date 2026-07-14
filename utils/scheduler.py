import random
from datetime import datetime, timedelta


def generate_schedule(
    end_date: datetime,
    count: int,
    shuffle: bool = False,
    _now: datetime = None,
) -> list:
    """
    Distributes `count` pins evenly across:
        range_start = now + 2 hours
        range_end   = end_date 23:59:59

    interval = total_seconds / count, rounded to nearest minute.
    Strictly deterministic, no jitter.

    shuffle=True  → waktu slot diacak urutannya, sehingga konten pin
                    yang di-assign ke index 0,1,2,... tidak selalu
                    rilis di urutan kronologis.
    shuffle=False → default, slot dikembalikan urut kronologis.
    """
    now         = _now or datetime.now()
    range_start = now.replace(second=0, microsecond=0) + timedelta(hours=2)
    range_end   = end_date.replace(hour=23, minute=59, second=59, microsecond=0)

    if range_start >= range_end:
        raise ValueError("range_start (now+2h) must be before end_date 23:59:59")
    if count <= 0:
        raise ValueError("count must be a positive integer")

    total_seconds    = (range_end - range_start).total_seconds()
    interval_sec     = total_seconds / count
    interval_rounded = round(interval_sec / 60) * 60

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

    fake_now = datetime(2025, 1, 1, 10, 0, 0)

    print("=== shuffle=False (default) ===")
    pprint(generate_schedule(datetime(2025, 1, 3), count=10, _now=fake_now))

    print("\n=== shuffle=True ===")
    pprint(generate_schedule(datetime(2025, 1, 3), count=10, shuffle=True, _now=fake_now))
