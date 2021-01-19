from celery import shared_task
from datetime import datetime
from django.utils import timezone
import pytz
import feedparser
import logging
import re
from dateutil.parser import parse
from .models import Event, EventImport, Owner

from .app_settings import OPCALENDAR_TASKS_TIME_LIMIT
from bravado.exception import HTTPBadGateway, HTTPGatewayTimeout, HTTPServiceUnavailable
from allianceauth.services.tasks import QueueOnce
from ics import Calendar
import requests

import random


from celery import shared_task

from allianceauth.services.hooks import get_extension_logger
from allianceauth.services.tasks import QueueOnce
from esi.models import Token


DEFAULT_TASK_PRIORITY = 6


DEFAULT_TASK_PRIORITY = 6

logger = logging.getLogger(__name__)

# Create your tasks here
TASK_DEFAULT_KWARGS = {
    "time_limit": OPCALENDAR_TASKS_TIME_LIMIT,
}

TASK_ESI_KWARGS = {
    **TASK_DEFAULT_KWARGS,
    **{
        "bind": True,
        "autoretry_for": (
            OSError,
            HTTPBadGateway,
            HTTPGatewayTimeout,
            HTTPServiceUnavailable,
        ),
        "retry_kwargs": {"max_retries": 3},
        "retry_backoff": 30,
    },
}



# Import eve uni classes
@shared_task
def import_fleets():
	
	#Clear out all fleets to remove deleted fleets
	Event.objects.filter(visibility="import").delete()

	local_tz = pytz.timezone("UTC") 

	#Get all import feeds
	feeds = EventImport.objects.all()
	
	for feed in feeds:
		if feed.source=="Spectre Fleet":

			#Get fleets from SF RSS
			d = feedparser.parse('https://www.spectre-fleet.space/engagement/events/rss')
			for entry in d.entries:
				##Look for SF fleets only
				if entry.author_detail.name=='Spectre Fleet':
					#Only active fleets
					if not "[RESERVED]" in entry.title:

						date_object = datetime.strptime(entry.published,'%a, %d %b %Y %H:%M:%S %z')
						date_object.strftime('%Y-%m-%dT%H:%M')

						event = Event(
							operation_type=feed.operation_type,
							title=entry.title,
							host=feed.host,
							doctrine="",
							formup_system="",
							description=entry.description,
							start_time=date_object, 
							end_time=date_object, 
							fc="",
							visibility="import",
							user_id = feed.creator.id,
							eve_character_id = feed.eve_character.id
						)
						event.save()

		if feed.source=="EVE University":
			#Get fleets from EVE UNI Ical
			url = "https://portal.eveuniversity.org/api/getcalendar"
			c = Calendar(requests.get(url).text)
			for entry in c.events:
				#Filter only class events as they are the only public events in eveuni
				
				if "class" in entry.name.lower():		
					event = Event(
						operation_type=feed.operation_type,
						title=re.sub("[\(\[].*?[\)\]]", "", entry.name),
						host=feed.host,
						doctrine="",
						formup_system="",
						description=entry.description,
						start_time=datetime.utcfromtimestamp(entry.begin.timestamp).replace(tzinfo=pytz.utc), 
						end_time=datetime.utcfromtimestamp(entry.end.timestamp).replace(tzinfo=pytz.utc), 
						fc="",
						visibility="import",
						user_id = feed.creator.id,
						eve_character_id = feed.eve_character.id
					)
					event.save()

@shared_task(
    **{
        **TASK_ESI_KWARGS,
        **{
            "base": QueueOnce,
            "once": {"keys": ["owner_pk"], "graceful": True},
            "max_retries": None,
        },
    }
)
def update_events_for_owner(self, owner_pk):
    """fetches all calendars for owner from ESI"""
    print(owner_pk)
    return _get_owner(owner_pk).update_events_esi()

@shared_task(**TASK_DEFAULT_KWARGS)
def update_all_ingame_events():
    for owner in Owner.objects.all():
        update_events_for_owner.apply_async(
            kwargs={"owner_pk": owner.pk},
            priority=DEFAULT_TASK_PRIORITY,
        )


def _get_owner(owner_pk: int) -> Owner:
    """returns the owner or raises exception"""
    try:
        owner = Owner.objects.get(pk=owner_pk)
    except Owner.DoesNotExist:
        raise Owner.DoesNotExist(
            "Requested owner with pk {} does not exist".format(owner_pk)
        )
    return owner


@shared_task
def add(x, y):
    return x + y

   