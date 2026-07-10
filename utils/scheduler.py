import random
from datetime import datetime, timedelta


def generate_schedule(start_date: datetime, end_date: datetime, count: int, hour_start: int = 9, hour_end: int = 21) -> list:
    if start_date > end_date:
        raise ValueError("Start date must be before end date")

    total_days = (end_date - start_date).days + 1
    available_slots = []

    for day_offset in range(total_days):
        day = start_date + timedelta(days=day_offset)
        for hour in range(hour_start, hour_end + 1):
            minute = random.choice([0, 15, 30, 45])
            slot = day.replace(hour=hour, minute=minute, second=0)
            available_slots.append(slot)

    if count > len(available_slots):
        raise ValueError(f"Not enough slots ({len(available_slots)}) for {count} pins in the given date range.")

    chosen = sorted(random.sample(available_slots, count))
    return [dt.strftime("%Y-%m-%dT%H:%M:%S") for dt in chosen]
