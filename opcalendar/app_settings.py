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

