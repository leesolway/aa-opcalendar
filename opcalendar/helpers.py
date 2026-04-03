import datetime

from django.utils import timezone


def get_tz_offset_string(tz_name: str) -> str:
    """Return a UTC offset string like 'UTC+05:30' for a given IANA tz name."""
    from datetime import datetime as _dt, timezone as dt_timezone
    try:
        from zoneinfo import ZoneInfo
        now_utc = _dt.now(dt_timezone.utc)
        offset = now_utc.astimezone(ZoneInfo(tz_name)).utcoffset()
    except Exception:
        offset = None
    if offset is None:
        return "UTC\u00b100:00"
    total_minutes = int(offset.total_seconds() // 60)
    sign = "+" if total_minutes >= 0 else "-"
    total_minutes = abs(total_minutes)
    return f"UTC{sign}{total_minutes // 60:02d}:{total_minutes % 60:02d}"


class time_helpers:
    @staticmethod
    def convert_timedelta(duration):
        # days = duration.days
        seconds = duration.seconds

        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60

        return hours, minutes, seconds

    @staticmethod
    def format_timedelta(td):
        hours, minutes, seconds = time_helpers.convert_timedelta(td)
        return "%d Days, %d Hours, %d Min" % (td.days, round(hours), round(minutes))

    @staticmethod
    def get_time_until(dt):
        """Return D / H / M Until DateTime"""
        return time_helpers.format_timedelta(
            dt.replace(tzinfo=timezone.utc) - datetime.datetime.now(timezone.utc)
        )
