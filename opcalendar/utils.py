# calendarapp/utils.py

from datetime import datetime, timedelta, date, timezone
from calendar import HTMLCalendar
from .models import Event, IngameEvents
from eventcalendar.helper import get_current_user
from typing import Any
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

class Calendar(HTMLCalendar):
	def __init__(self, year=None, month=None, user=None):
		self.year = year
		self.month = month
		self.user = user
		super(Calendar, self).__init__()
		
	# formats a day as a td
	# filter events by day
	def formatday(self, day, events, ingame_events):
		events_per_day = events.filter(start_time__day=day).order_by('start_time')
		ingame_events_per_day = ingame_events.filter(event_start_date__day=day).order_by('event_start_date')
		d = ''
		
		# Only events for current month
		if day != 0:
			# Parse events
			for event in events_per_day:
				#Display public events
				if event.visibility == "public" or event.visibility == "import" and self.user.has_perm('opcalendar.view_public'):
					#Get past events
					if datetime.now(timezone.utc) > event.start_time:
						d += f'<a class="nostyling" href="{event.get_html_url}"><div class="event {event.get_html_operation_color} past-event {event.visibility}-event">{event.get_html_title}</div></a>'
					if datetime.now(timezone.utc) <= event.start_time:
						d += f'<a class="nostyling" href="{event.get_html_url}"><div class="event {event.get_html_operation_color} {event.visibility}-event">{event.get_html_title}</div></a>'
				if event.visibility == "member" and self.user.has_perm('opcalendar.view_member'):
					#Get past events
					if datetime.now(timezone.utc) > event.start_time:
						d += f'<a class="nostyling" href="{event.get_html_url}"><div class="event {event.get_html_operation_color} past-event {event.visibility}-event">{event.get_html_title}</div></a>'
					if datetime.now(timezone.utc) <= event.start_time:
						d += f'<a class="nostyling" href="{event.get_html_url}"><div class="event {event.get_html_operation_color} {event.visibility}-event">{event.get_html_title}</div></a>'
			for event in ingame_events_per_day:
				if self.user.has_perm('opcalendar.view_ingame'):
					#Get past events
					if datetime.now(timezone.utc) > event.event_start_date:
						d += f'<a class="nostyling" href="{event.get_html_url}"><div class="event {event.get_html_operation_color} past-event import-event">{event.get_html_title}</div></a>'
					if datetime.now(timezone.utc) <= event.event_start_date:
						d += f'<a class="nostyling" href="{event.get_html_url}"><div class="event {event.get_html_operation_color} import-event">{event.get_html_title}</div></a>'

			if date.today() == date(self.year, self.month, day):
				return f"<td class='today'><div class='date'>{day}</div> {d}</td>"
			return f"<td><div class='date'>{day}</div> {d}</td>"
		return '<td></td>'

	# formats a week as a tr 
	def formatweek(self, theweek, events, ingame_events):
		week = ''
		for d, weekday in theweek:
			week += self.formatday(d, events, ingame_events)
		return f'<tr> {week} </tr>'

	# formats a month as a table
	# filter events by year and month
	def formatmonth(self, withyear=True):
		events = Event.objects.filter(start_time__year=self.year, start_time__month=self.month)
		ingame_events = IngameEvents.objects.filter(event_start_date__year=self.year, event_start_date__month=self.month)
		
		cal = f'<table border="0" cellpadding="0" cellspacing="0" class="calendar">\n'
		cal += f'{self.formatmonthname(self.year, self.month, withyear=withyear)}\n'
		cal += f'{self.formatweekheader()}\n'
		for week in self.monthdays2calendar(self.year, self.month):
			cal += f'{self.formatweek(week, events, ingame_events)}\n'
		return cal

def clean_setting(
    name: str,
    default_value: object,
    min_value: int = None,
    max_value: int = None,
    required_type: type = None,
    choices: list = None,
) -> Any:
    """cleans the input for a custom setting

    Will use `default_value` if settings does not exit or has the wrong type
    or is outside define boundaries (for int only)

    Need to define `required_type` if `default_value` is `None`

    Will assume `min_value` of 0 for int (can be overriden)

    `None` allowed as value

    Returns cleaned value for setting
    """
    if default_value is None and not required_type:
        raise ValueError("You must specify a required_type for None defaults")

    if not required_type:
        required_type = type(default_value)

    if min_value is None and required_type == int:
        min_value = 0

    if not hasattr(settings, name):
        cleaned_value = default_value
    else:
        dirty_value = getattr(settings, name)
        if dirty_value is None or (
            isinstance(dirty_value, required_type)
            and (min_value is None or dirty_value >= min_value)
            and (max_value is None or dirty_value <= max_value)
            and (choices is None or dirty_value in choices)
        ):
            cleaned_value = dirty_value
        else:
            logger.warn(
                "You setting for {} it not valid. Please correct it. "
                "Using default for now: {}".format(name, default_value)
            )
            cleaned_value = default_value
    return cleaned_value

