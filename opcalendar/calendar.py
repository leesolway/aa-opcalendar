import operator
from calendar import HTMLCalendar
from datetime import date
from itertools import chain

from django.db.models import Q, F

from allianceauth.services.hooks import get_extension_logger

from .models import Event, IngameEvents
from .app_settings import (
    OPCALENDAR_DISPLAY_STRUCTURETIMERS,
)

from .app_settings import structuretimers_active

if structuretimers_active():
    from structuretimers.models import Timer

logger = get_extension_logger(__name__)


class Calendar(HTMLCalendar):
    def __init__(self, year=None, month=None, user=None):
        self.year = year
        self.month = month
        self.user = user
        super(Calendar, self).__init__()

    # formats a day as a td
    # filter events by day
    def formatday(self, day, events, ingame_events, structuretimer_events):

        events_per_day = events.filter(start_time__day=day)

        ingame_events_per_day = ingame_events.filter(event_start_date__day=day)

        structuretimers_per_day = structuretimer_events.filter(start_time__day=day)

        all_events_per_day = sorted(
            chain(events_per_day, ingame_events_per_day, structuretimers_per_day),
            key=operator.attrgetter("start_time"),
        )

        d = ""

        # Only events for current month
        if day != 0:
            # Parse events
            for event in all_events_per_day:

                if not type(event).__name__ == "Timer":
                    d += (
                        f"<style>{event.get_event_styling}</style>"
                        f'<a class="nostyling" href="{event.get_html_url}">'
                        f'<div class="event {event.get_date_status} {event.get_visibility_class} {event.get_category_class}">{event.get_html_title}</div>'
                        f"</a>"
                    )
                if type(event).__name__ == "Timer":
                    d += f'<div class="event event-structuretimer">{event.date.strftime("%H:%M")}<i> Structure timer: {event.structure_name}</i></div>'

            if date.today() == date(self.year, self.month, day):
                return f"<td class='today'><div class='date'>{day}</div> {d}</td>"
            return f"<td><div class='date'>{day}</div> {d}</td>"
        return "<td></td>"

    # formats a week as a tr
    def formatweek(self, theweek, events, ingame_events, structuretimer_events):
        week = ""
        for d, weekday in theweek:
            week += self.formatday(d, events, ingame_events, structuretimer_events)
        return f"<tr> {week} </tr>"

    # formats a month as a table
    # filter events by year and month

    def formatmonth(self, withyear=True):
        # Get normal events
        # Filter by groups and states
        events = (
            Event.objects.filter(
                start_time__year=self.year,
                start_time__month=self.month,
            )
            .filter(
                Q(event_visibility__restricted_to_group__in=self.user.groups.all())
                | Q(event_visibility__restricted_to_group__isnull=True),
            )
            .filter(
                Q(event_visibility__restricted_to_state=self.user.profile.state)
                | Q(event_visibility__restricted_to_state__isnull=True),
            )
        )
        # Get ingame events
        # Filter by groups and states
        ingame_events = (
            IngameEvents.objects.filter(
                event_start_date__year=self.year, event_start_date__month=self.month
            )
            .annotate(start_time=F("event_start_date"), end_time=F("event_end_date"))
            .filter(
                Q(
                    owner__event_visibility__restricted_to_group__in=self.user.groups.all()
                )
                | Q(owner__event_visibility__restricted_to_group__isnull=True),
            )
            .filter(
                Q(owner__event_visibility__restricted_to_state=self.user.profile.state)
                | Q(owner__event_visibility__restricted_to_state__isnull=True),
            )
        )

        # Check if structuretimers is active
        # Should we fetch timers
        if structuretimers_active() and OPCALENDAR_DISPLAY_STRUCTURETIMERS:
            structuretimer_events = (
                Timer.objects.all()
                .visible_to_user(self.user)
                .annotate(start_time=F("date"))
                .filter(date__year=self.year, date__month=self.month)
            )
        else:
            structuretimer_events = Event.objects.none()

        logger.debug(
            "Returning %s structure timers, display setting is %s"
            % (structuretimer_events.count(), OPCALENDAR_DISPLAY_STRUCTURETIMERS)
        )

        logger.debug("Returning %s events" % ingame_events.count())

        cal = '<table class="calendar">\n'
        cal += f"{self.formatmonthname(self.year, self.month, withyear=withyear)}\n"
        cal += f"{self.formatweekheader()}\n"

        for week in self.monthdays2calendar(self.year, self.month):
            cal += f"{self.formatweek(week, events, ingame_events, structuretimer_events)}\n"

        cal += "</table>"

        return cal
