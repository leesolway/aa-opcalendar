from django.conf import settings
from .utils import clean_setting
import re

def get_site_url():  # regex sso url
    regex = r"^(.+)\/s.+"
    matches = re.finditer(regex, settings.ESI_SSO_CALLBACK_URL, re.MULTILINE)
    url = "http://"

    for m in matches:
        url = m.groups()[0] # first match

    return url

# Hard timeout for tasks in seconds to reduce task accumulation during outages
OPCALENDAR_TASKS_TIME_LIMIT = clean_setting("OPCALENDAR_TASKS_TIME_LIMIT", 7200)

# whether admins will get notifications about import events
OPCALENDAR_ADMIN_NOTIFICATIONS_ENABLED = clean_setting(
    "OPCALENDAR_ADMIN_NOTIFICATIONS_ENABLED", True
)

# whether we should send out discord notifications for imported fleets
OPCALENDAR_NOTIFY_IMPORTS = clean_setting(
    "OPCALENDAR_NOTIFY_IMPORTS", True
)

OPCALENDAR_EVE_UNI_URL = "https://portal.eveuniversity.org/api/getcalendar"
OPCALENDAR_SPECTRE_URL = "https://www.spectre-fleet.space/engagement/events/rss"
