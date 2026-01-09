from datetime import datetime, timedelta

def get_msk_time(dt: datetime = None) -> datetime:
    """Converts UTC datetime to MSK (UTC+3) or gets current MSK time."""
    if dt is None:
        # If naive, assume UTC for now or just take utcnow
        dt = datetime.utcnow()
    return dt + timedelta(hours=3)

def format_dt(dt: datetime) -> str:
    """Formats datetime to string in MSK."""
    if not dt:
        return "Никогда"
    return get_msk_time(dt).strftime("%d.%m.%Y %H:%M")
