from datetime import datetime


DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_today_str():
    return datetime.now().strftime(DATE_FORMAT)


def get_now_datetime():
    return datetime.now()


def get_now_str():
    return get_now_datetime().strftime(DATETIME_FORMAT)


def format_datetime(value):
    if hasattr(value, "strftime"):
        return value.strftime(DATETIME_FORMAT)

    return str(value)
