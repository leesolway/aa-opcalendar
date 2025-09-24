from datetime import datetime, timezone as dt_timezone
from zoneinfo import ZoneInfo

from django import template

from opcalendar.models import UserSettings

register = template.Library()


def _format_offset(tz_name: str) -> str:
    try:
        now_utc = datetime.now(dt_timezone.utc)
        offset = now_utc.astimezone(ZoneInfo(tz_name)).utcoffset()
    except Exception:
        offset = None
    if offset is None:
        return "UTC±00:00"
    total_minutes = int(offset.total_seconds() // 60)
    sign = "+" if total_minutes >= 0 else "-"
    total_minutes = abs(total_minutes)
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"UTC{sign}{hours:02d}:{minutes:02d}"


@register.simple_tag(takes_context=True)
def opcalendar_active_tz(context):
    """
    Return a dict with the active timezone name and current UTC offset for the logged-in user.
    Fallback to UTC if no user setting exists.
    Usage:
        {% opcalendar_active_tz as tz %}
        {{ tz.name }} {{ tz.offset }}
    """
    request = context.get("request")
    tz_name = "UTC"
    if request and getattr(request, "user", None) and request.user.is_authenticated:
        try:
            us = UserSettings.objects.get(user=request.user)
            if us.timezone:
                tz_name = us.timezone
        except UserSettings.DoesNotExist:
            pass
    return {"name": tz_name, "offset": _format_offset(tz_name)}
