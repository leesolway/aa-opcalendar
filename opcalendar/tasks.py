from datetime import datetime
import pytz
import feedparser
import re
from .models import Event, EventImport, Owner

from .app_settings import OPCALENDAR_TASKS_TIME_LIMIT
from bravado.exception import HTTPBadGateway, HTTPGatewayTimeout, HTTPServiceUnavailable
from ics import Calendar
import requests


from celery import shared_task

from allianceauth.services.hooks import get_extension_logger
from allianceauth.services.tasks import QueueOnce

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


# Import NPSI fleets
@shared_task
def import_all_npsi_fleets():

    # Get all current imported fleets in database
    event_ids_to_remove = list(
        Event.objects.filter(visibility="import").values_list("id", flat=True)
    )

    # Get all import feeds
    feeds = EventImport.objects.all()

    feed_errors = False

    # Check for active NPSI feeds
    for feed in feeds:

        # If Spectre Fleet is active
        if feed.source == "Spectre Fleet":

            logger.debug(
                "Spectre: import feed active. Pulling events from %s"
                % OPCALENDAR_SPECTRE_URL
            )

            try:

                # Get spectre fleets from ther RSS feed
                d = feedparser.parse(OPCALENDAR_SPECTRE_URL)

                # Process each fleet entry
                for entry in d.entries:

                    # Look for SF fleets only
                    if entry.author_detail.name == "Spectre Fleet":

                        # Only active fleets
                        if "[RESERVED]" not in entry.title:

                            logger.debug("Spectre: Import even found: %s" % entry.title)

                            # Format datetimes
                            date_object = datetime.strptime(
                                entry.published, "%a, %d %b %Y %H:%M:%S %z"
                            )
                            date_object.strftime("%Y-%m-%dT%H:%M")

                            # Check if we already have the event stored
                            original = Event.objects.filter(
                                start_time=date_object, title=entry.title
                            ).first()

                            logger.debug(
                                "Spectre: Got match from database: %s" % original
                            )

                            # If we get the event from API it should not be removed
                            if original is not None:

                                logger.debug(
                                    "Spectre: Event: %s already in database"
                                    % entry.title
                                )

                                # Remove the found fleet from the to be removed list
                                event_ids_to_remove.remove(original.id)

                            else:
                                # Save new fleet to database
                                event = Event(
                                    operation_type=feed.operation_type,
                                    title=entry.title,
                                    host=feed.host,
                                    doctrine="see details",
                                    formup_system=feed.source,
                                    description=entry.description,
                                    start_time=date_object,
                                    end_time=date_object,
                                    fc=feed.source,
                                    visibility="import",
                                    user_id=feed.creator.id,
                                    eve_character_id=feed.eve_character.id,
                                )

                                logger.debug(
                                    "Spectre: Saved new event in database: %s"
                                    % entry.title
                                )

                                event.save()
            except Exception as ex:
                logger.error("Spectre: Error in fetching fleets", exc_info=True)
                feed_errors = True
                raise ex

        # Check for FUN Inc fleets
        if feed.source == "Fun Inc.":
            logger.debug(
                "Fun Inc: import feed active. Pulling events from %s"
                % OPCALENDAR_FUNINC_URL
            )

            try:
                # Get FUN Inc fleets from google ical
                url = OPCALENDAR_FUNINC_URL
                c = Calendar(requests.get(url).text)

                # Check if ical file loaded correctly with events
                if not c:
                    feed_errors = True
                    raise Exception(
                        "Fun Inc: Error fetching calendar events, list is empty."
                    )

                # Parse each entry we got
                for entry in c.events:

                    # Format datetime
                    start_date = datetime.utcfromtimestamp(
                        entry.begin.timestamp
                    ).replace(tzinfo=pytz.utc)
                    end_date = datetime.utcfromtimestamp(entry.end.timestamp).replace(
                        tzinfo=pytz.utc
                    )
                    title = entry.name

                    logger.debug("Fun Inc: Import even found: %s" % title)

                    # Check if we already have the event stored
                    original = Event.objects.filter(
                        start_time=start_date, title=title
                    ).first()

                    logger.debug("Fun Inc: Got match from database: %s" % original)

                    # If we get the event from API it should not be removed
                    if original is not None:

                        logger.debug("Fun Inc: Event: %s already in database" % title)

                        # Remove the found fleet from the to be removed list
                        event_ids_to_remove.remove(original.id)

                    else:
                        # Save new fleet to database
                        event = Event(
                            operation_type=feed.operation_type,
                            title=title,
                            host=feed.host,
                            doctrine="see details",
                            formup_system=feed.source,
                            description=entry.description,
                            start_time=start_date,
                            end_time=end_date,
                            fc=feed.source,
                            visibility="import",
                            user_id=feed.creator.id,
                            eve_character_id=feed.eve_character.id,
                        )

                        logger.debug(
                            "Fun Inc: Saved new EVE UNI event in database: %s" % title
                        )

                        event.save()

            except Exception as ex:
                logger.error("Spectre: Error in fetching fleets", exc_info=True)
                feed_errors = True
                raise ex

        # Check for EVE Uni events
        if feed.source == "EVE University":
            logger.debug(
                "EVE Uni: import feed active. Pulling events from %s"
                % OPCALENDAR_EVE_UNI_URL
            )

            try:
                # Get EVE Uni events from their API feed (ical)
                url = OPCALENDAR_EVE_UNI_URL
                c = Calendar(requests.get(url).text)
                for entry in c.events:

                    # Filter only class events as they are the only public events in eveuni
                    if "class" in entry.name.lower():

                        # Format datetime
                        start_date = datetime.utcfromtimestamp(
                            entry.begin.timestamp
                        ).replace(tzinfo=pytz.utc)
                        end_date = datetime.utcfromtimestamp(
                            entry.end.timestamp
                        ).replace(tzinfo=pytz.utc)
                        title = re.sub(r"[\(\[].*?[\)\]]", "", entry.name)

                        logger.debug("EVE Uni: Import even found: %s" % title)

                        # Check if we already have the event stored
                        original = Event.objects.filter(
                            start_time=start_date, title=title
                        ).first()

                        logger.debug("EVE Uni: Got match from database: %s" % original)

                        # If we get the event from API it should not be removed
                        if original is not None:

                            logger.debug(
                                "EVE Uni: Event: %s already in database" % title
                            )

                            # Remove the found fleet from the to be removed list
                            event_ids_to_remove.remove(original.id)

                        else:
                            # Save new event to database
                            event = Event(
                                operation_type=feed.operation_type,
                                title=title,
                                host=feed.host,
                                doctrine="see details",
                                formup_system=feed.source,
                                description=entry.description,
                                start_time=start_date,
                                end_time=end_date,
                                fc=feed.source,
                                visibility="import",
                                user_id=feed.creator.id,
                                eve_character_id=feed.eve_character.id,
                            )

                            logger.debug(
                                "EVE Uni: Saved new EVE UNI event in database: %s"
                                % title
                            )
                            event.save()

            except Exception as ex:
                logger.error("Spectre: Error in fetching fleets", exc_info=True)
                feed_errors = True
                raise ex

    logger.debug("Checking for NPSI fleets to be removed.")

    if feed_errors:
        logger.error("Errors in feeds, not cleaning up operations on this run")
    else:
        if not event_ids_to_remove:
            logger.debug("No NPSI fleets to be removed.")
        else:
            logger.debug("Removed unseen NPSI fleets")
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
