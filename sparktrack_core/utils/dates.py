from datetime import date, datetime


def display_date(value: date | datetime | None) -> str:
    if value is None:
        return ""
    return value.strftime("%Y-%m-%d")


def display_datetime(value: datetime | None) -> str:
    if value is None:
        return ""
    return value.strftime("%Y-%m-%d %H:%M")
