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

from .app_settings import (
    OPCALENDAR_EVE_UNI_URL,
    OPCALENDAR_SPECTRE_URL,
    OPCALENDAR_FUNINC_URL,
)

DEFAULT_TASK_PRIORITY = 6

logger = get_extension_logger(__name__)

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
	
	#Get all current imported fleets in database
	event_ids_to_remove = list(
    	Event.objects.filter(visibility="import").values_list("id", flat=True)
    )
	local_tz = pytz.timezone("UTC")

	#Get all import feeds
	feeds = EventImport.objects.all()
	
	for feed in feeds:
		if feed.source=="Spectre Fleet":
			logger.debug("Spectre: import feed active. Pulling events from %s" % OPCALENDAR_SPECTRE_URL)
			#Get fleets from SF RSS
			d = feedparser.parse(OPCALENDAR_SPECTRE_URL)
			for entry in d.entries:
				##Look for SF fleets only
				if entry.author_detail.name=='Spectre Fleet':
					#Only active fleets
					if not "[RESERVED]" in entry.title:

						logger.debug("Spectre: Import even found: %s" % entry.title)
						
						date_object = datetime.strptime(entry.published,'%a, %d %b %Y %H:%M:%S %z')
						date_object.strftime('%Y-%m-%dT%H:%M')

						# Check if we already have the event stored
						original = Event.objects.filter(start_time=date_object, title=entry.title).first()

						#If we get the event from API it should not be removed
						if original is not None:
							logger.debug("Spectre: Event: %s already in database" % entry.title)
							event_ids_to_remove.remove(original.id)

						else:
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
							
							logger.debug("Spectre: Saved new event in database: %s" % entry.title)
							
							event.save()

		if feed.source=="EVE University":
			logger.debug("EVE Uni: import feed active. Pulling events from %s" % OPCALENDAR_EVE_UNI_URL)
			#Get fleets from EVE UNI Ical
			url = OPCALENDAR_FUNINC_URL
			c = Calendar(requests.get(url).text)
			for entry in c.events:
				#Filter only class events as they are the only public events in eveuni
				
				if "class" in entry.name.lower():

					start_date = datetime.utcfromtimestamp(entry.begin.timestamp).replace(tzinfo=pytz.utc)
					end_date = datetime.utcfromtimestamp(entry.end.timestamp).replace(tzinfo=pytz.utc)
					title = re.sub("[\(\[].*?[\)\]]", "", entry.name)

					logger.debug("EVE Uni: Import even found: %s" % title)

					# Check if we already have the event stored
					original = Event.objects.filter(start_time=start_date, title=title).first()

					#If we get the event from API it should not be removed	
					if original is not None:
						logger.debug("EVE Uni: Event: %s already in database" % title)
						event_ids_to_remove.remove(original.id)

					else:		
						event = Event(
							operation_type=feed.operation_type,
							title=title,
							host=feed.host,
							doctrine="",
							formup_system="",
							description=entry.description,
							start_time=start_date, 
							end_time=end_date, 
							fc="",
							visibility="import",
							user_id = feed.creator.id,
							eve_character_id = feed.eve_character.id
						)

						logger.debug("EVE Uni: Saved new EVE UNI event in database: %s" % title)
						event.save()

		if feed.source=="Fun Inc.":
			logger.debug("FUN INC: import feed active. Pulling events from %s" % OPCALENDAR_EVE_UNI_URL)
			#Get fleets from EVE UNI Ical
			url = OPCALENDAR_EVE_UNI_URL
			c = Calendar(requests.get(url).text)
			for entry in c.events:

				start_date = datetime.utcfromtimestamp(entry.begin.timestamp).replace(tzinfo=pytz.utc)
				end_date = datetime.utcfromtimestamp(entry.end.timestamp).replace(tzinfo=pytz.utc)
				title = re.sub("[\(\[].*?[\)\]]", "", entry.name)

				logger.debug("FUN INC: Import even found: %s" % title)

				# Check if we already have the event stored
				original = Event.objects.filter(start_time=start_date, title=title).first()

				#If we get the event from API it should not be removed	
				if original is not None:
					logger.debug("FUN INC: Event: %s already in database" % title)
					event_ids_to_remove.remove(original.id)

				else:		
					event = Event(
						operation_type=feed.operation_type,
						title=title,
						host=feed.host,
						doctrine="",
						formup_system="",
						description=entry.description,
						start_time=start_date, 
						end_time=end_date, 
						fc="",
						visibility="import",
						user_id = feed.creator.id,
						eve_character_id = feed.eve_character.id
					)

					logger.debug("FUN INC: Saved new FUN INC. event in database: %s" % title)
					event.save()

	logger.debug("Removing all events that we did not get over API")
	# Remove all events we did not see from API					
	Event.objects.filter(pk__in=event_ids_to_remove).delete()

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

   