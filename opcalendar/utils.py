# calendarapp/utils.py

from datetime import datetime, timedelta, date, timezone
from calendar import HTMLCalendar
from .models import Event
from eventcalendar.helper import get_current_user

from django.utils.translation import ugettext_lazy as _

class Calendar(HTMLCalendar):
	def __init__(self, year=None, month=None, user=None):
		self.year = year
		self.month = month
		self.user = user
		super(Calendar, self).__init__()
		
	# formats a day as a td
	# filter events by day
	def formatday(self, day, events):
		events_per_day = events.filter(start_time__day=day).order_by('start_time')
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

			if date.today() == date(self.year, self.month, day):
				return f"<td class='today'><div class='date'>{day}</div> {d}</td>"
			return f"<td><div class='date'>{day}</div> {d}</td>"
		return '<td></td>'

	# formats a week as a tr 
	def formatweek(self, theweek, events):
		week = ''
		for d, weekday in theweek:
			week += self.formatday(d, events)
		return f'<tr> {week} </tr>'

	# formats a month as a table
	# filter events by year and month
	def formatmonth(self, withyear=True):
		events = Event.objects.filter(start_time__year=self.year, start_time__month=self.month)

		cal = f'<table border="0" cellpadding="0" cellspacing="0" class="calendar">\n'
		cal += f'{self.formatmonthname(self.year, self.month, withyear=withyear)}\n'
		cal += f'{self.formatweekheader()}\n'
		for week in self.monthdays2calendar(self.year, self.month):
			cal += f'{self.formatweek(week, events)}\n'
		return cal