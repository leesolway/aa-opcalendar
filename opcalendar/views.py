# cal/views.py
import calendar
from datetime import date, datetime, timedelta

from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from allianceauth.services.hooks import get_extension_logger
from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core import serializers
from django.db import Error, transaction
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView
from django_ical.views import ICalFeed
from esi.decorators import token_required
from zoneinfo import ZoneInfo
from django.utils import timezone

from opcalendar.models import (
    Event,
    EventCategory,
    EventMember,
    EventVisibility,
    IngameEvents,
    Owner,
    UserSettings,
)

from . import tasks
from .app_settings import (
    OPCALENDAR_DISPLAY_MOONMINING_ARRIVAL_TIME,
    get_site_url,
    moonmining_active,
    structuretimers_active,
)
from .calendar import Calendar
from .forms import EventEditForm, EventForm, UserSettingsForm
from .utils import messages_plus

logger = get_extension_logger(__name__)


@login_required(login_url="signup")
def index(request):
    return HttpResponse("hello")


@token_required(scopes=["esi-calendar.read_calendar_events.v1"])
def add_ingame_calendar(request, token):
    token_char = EveCharacter.objects.get(character_id=token.character_id)

    success = True
    try:
        owned_char = CharacterOwnership.objects.get(
            user=request.user, character=token_char
        )
    except CharacterOwnership.DoesNotExist:
        success = False
        owned_char = None

        messages_plus.error(
            request,
            format_html(
                gettext_lazy(
                    "You can only use your main or alt characters "
                    "to add corporations. "
                    "However, character %s is neither. "
                )
                % format_html("<strong>{}</strong>", token_char.character_name)
            ),
        )

    if success:
        try:
            corporation = EveCorporationInfo.objects.get(
                corporation_id=token_char.corporation_id
            )
        except EveCorporationInfo.DoesNotExist:
            corporation = EveCorporationInfo.objects.create_corporation(
                token_char.corporation_id
            )

        with transaction.atomic():
            owner, _ = Owner.objects.update_or_create(
                corporation=corporation, defaults={"character": owned_char}
            )

            owner.save()

        tasks.update_events_for_owner(owner_pk=owner.pk)

        messages_plus.success(
            request,
            format_html(
                gettext_lazy(
                    "Succesfully added ingame calendar sync for %(character)s. Process will run on background. You will receive a report once the process is finished."
                )
                % {
                    "corporation": format_html("<strong>{}</strong>", owner),
                    "character": format_html(
                        "<strong>{}</strong>", owner.character.character.character_name
                    ),
                }
            ),
        )

    return redirect("opcalendar:calendar")


def get_date(req_day):
    if req_day:
        year, month = (int(x) for x in req_day.split("-"))
        return date(year, month, day=1)
    return datetime.today()


def event_member_signup_attending(request, event_id):
    return handle_event_member_signup(request, event_id, EventMember.Status.ATTENDING)


def event_member_signup_maybe(request, event_id):
    return handle_event_member_signup(request, event_id, EventMember.Status.MAYBE)


def event_member_signup_declined(request, event_id):
    return handle_event_member_signup(request, event_id, EventMember.Status.DECLINED)


def handle_event_member_signup(request, event_id, status):
    event = get_object_or_404(Event, id=event_id)
    character = request.user.profile.main_character

    if request.method == "POST":
        comment = request.POST.get("comment", "")
        EventMember.objects.update_or_create(
            event=event,
            character=character,
            defaults={"status": status, "comment": comment},
        )
        return redirect("opcalendar:event-detail", event_id=event.id)

    return redirect("opcalendar:event-detail", event_id=event.id)


def event_member_remove(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    character = request.user.profile.main_character
    EventMember.objects.filter(event=event, character=character).delete()
    return redirect("opcalendar:event-detail", event_id=event.id)


class CalendarView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = "opcalendar.basic_access"
    login_url = "signup"
    model = Event
    template_name = "opcalendar/calendar.html"

    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super().get_context_data(**kwargs)
        d = get_date(self.request.GET.get("month", None))

        user_settings, created = UserSettings.objects.get_or_create(
            user=user,
            defaults={"disable_discord_notifications": False},
        )

        # Allow tz override via GET (?tz=Area/City), and persist it.
        tz_param = self.request.GET.get("tz")
        if tz_param:
            try:
                # Basic validation to avoid garbage values in DB
                if "/" in tz_param and len(tz_param) <= 64:
                    user_settings.timezone = tz_param
                    user_settings.save(update_fields=["timezone"])
            except Exception:
                pass

        active_tz = getattr(user_settings, "timezone", None) or "UTC"

        cal = Calendar(
            d.year,
            d.month,
            user,
            user_tz_name=active_tz,
        )

        html_cal, all_events_per_month = cal.formatmonth(withyear=True)
        context["moonmining_active"] = moonmining_active()
        context["structuretimers_active"] = structuretimers_active()
        context["category"] = EventCategory.objects.all()
        context["visibility"] = EventVisibility.objects.all()
        context["calendar"] = mark_safe(html_cal)
        context["all_events_per_month"] = all_events_per_month
        context["user_settings"] = user_settings
        # Add active tz banner data
        try:
            now_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
            offset = now_utc.astimezone(ZoneInfo(active_tz)).utcoffset()
            if offset is not None:
                total_minutes = int(offset.total_seconds() // 60)
                sign = "+" if total_minutes >= 0 else "-"
                total_minutes = abs(total_minutes)
                hours = total_minutes // 60
                minutes = total_minutes % 60
                active_tz_offset = f"UTC{sign}{hours:02d}:{minutes:02d}"
            else:
                active_tz_offset = "UTC±00:00"
        except Exception:
            active_tz_offset = "UTC±00:00"
        context["active_tz"] = active_tz
        context["active_tz_offset"] = active_tz_offset
        context["OPCALENDAR_DISPLAY_MOONMINING_ARRIVAL_TIME"] = (
            OPCALENDAR_DISPLAY_MOONMINING_ARRIVAL_TIME
        )

        return context


@login_required
@permission_required("opcalendar.create_event")
def create_event(request):
    form = EventForm(request.POST or None)
    # Determine user's active timezone (defaults to UTC)
    try:
        user_settings = UserSettings.objects.get(user=request.user)
        active_tz_name = user_settings.timezone or "UTC"
    except UserSettings.DoesNotExist:
        active_tz_name = "UTC"
    active_tz = ZoneInfo(active_tz_name)

    if request.POST and form.is_valid():
        event_count = 0

        # Get character
        character = request.user.profile.main_character
        operation_type = form.cleaned_data["operation_type"]
        title = form.cleaned_data["title"]
        host = form.cleaned_data["host"]
        doctrine = form.cleaned_data["doctrine"]
        formup_system = form.cleaned_data["formup_system"]
        description = form.cleaned_data["description"]
        start_time_local = form.cleaned_data["start_time"]  # naive, interpret as user's tz
        end_time_local = form.cleaned_data["end_time"]      # naive, interpret as user's tz
        repeat_event = form.cleaned_data["repeat_event"]
        repeat_times = form.cleaned_data["repeat_times"]
        fc = form.cleaned_data["fc"]
        event_visibility = form.cleaned_data["event_visibility"]

        # Check time_mode toggle: "eve" means times are already in UTC
        time_mode = request.POST.get("time_mode", "local")

        if time_mode == "eve":
            # Times entered as UTC — attach UTC tzinfo directly
            start_time_utc = start_time_local.replace(tzinfo=timezone.utc)
            end_time_utc = end_time_local.replace(tzinfo=timezone.utc)
        else:
            # Convert local naive to aware UTC
            start_time_utc = start_time_local.replace(tzinfo=active_tz).astimezone(timezone.utc)
            end_time_utc = end_time_local.replace(tzinfo=active_tz).astimezone(timezone.utc)

        # Add original event to objects list
        event = Event(
            user=request.user,
            operation_type=operation_type,
            title=title,
            host=host,
            doctrine=doctrine,
            formup_system=formup_system,
            description=description,
            start_time=start_time_utc,
            end_time=end_time_utc,
            repeat_event=repeat_event,
            repeat_times=repeat_times,
            eve_character=character,
            fc=fc,
            event_visibility=event_visibility,
        )

        try:
            event.save()
        except Error as e:
            logger.error("Error creating event %s: %s" % (event, e))

        # If we have a repeating event add event to object list multiple times
        if repeat_event:
            logger.debug("Event repeat %s for %s times" % (repeat_event, repeat_times))
            start_local = start_time_local
            end_local = end_time_local
            for repeat in range(repeat_times):
                if repeat_event == "DD":
                    start_local += relativedelta(days=1)
                    end_local += relativedelta(days=1)
                if repeat_event == "WE":
                    start_local += relativedelta(weeks=1)
                    end_local += relativedelta(weeks=1)
                if repeat_event == "FN":
                    start_local += relativedelta(weeks=2)
                    end_local += relativedelta(weeks=2)
                if repeat_event == "MM":
                    start_local += relativedelta(months=1)
                    end_local += relativedelta(months=1)
                if repeat_event == "YY":
                    start_local += relativedelta(years=1)
                    end_local += relativedelta(years=1)

                # Convert each occurrence to UTC when saving
                if time_mode == "eve":
                    repeat_start_utc = start_local.replace(tzinfo=timezone.utc)
                    repeat_end_utc = end_local.replace(tzinfo=timezone.utc)
                else:
                    repeat_start_utc = start_local.replace(tzinfo=active_tz).astimezone(timezone.utc)
                    repeat_end_utc = end_local.replace(tzinfo=active_tz).astimezone(timezone.utc)

                event = Event(
                    user=request.user,
                    operation_type=operation_type,
                    title=title,
                    host=host,
                    doctrine=doctrine,
                    formup_system=formup_system,
                    description=description,
                    start_time=repeat_start_utc,
                    end_time=repeat_end_utc,
                    repeat_event=repeat_event,
                    repeat_times=repeat_times,
                    eve_character=character,
                    fc=fc,
                    event_visibility=event_visibility,
                )

                event_count += 1

                try:
                    event.save()
                except Error as e:
                    logger.error("Error creating event %s: %s" % (event, e))

        if event_count == 0:
            messages.success(
                request,
                ("Event %(opname)s created for %(date)s (%(tz)s).")
                % {
                    "opname": title,
                    "date": start_time_local.strftime("%Y-%m-%d %H:%M"),
                    "tz": active_tz_name,
                },
            )
        else:
            messages.success(
                request,
                (
                    "Event %(opname)s created for %(date)s (%(tz)s). %(event_count)s duplicated events created."
                )
                % {
                    "opname": title,
                    "date": start_time_local.strftime("%Y-%m-%d %H:%M"),
                    "tz": active_tz_name,
                    "event_count": event_count,
                },
            )

        return HttpResponseRedirect(reverse("opcalendar:calendar"))

    # Pass active timezone to template for hinting
    # Build an offset label like UTC+02:00
    try:
        now_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
        offset = now_utc.astimezone(active_tz).utcoffset()
        if offset is not None:
            total_minutes = int(offset.total_seconds() // 60)
            sign = "+" if total_minutes >= 0 else "-"
            total_minutes = abs(total_minutes)
            hours = total_minutes // 60
            minutes = total_minutes % 60
            active_tz_offset = f"UTC{sign}{hours:02d}:{minutes:02d}"
        else:
            active_tz_offset = "UTC±00:00"
    except Exception:
        active_tz_offset = None

    # Compute numeric offset in minutes for JS timezone conversion
    try:
        now_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
        offset = now_utc.astimezone(active_tz).utcoffset()
        active_tz_offset_minutes = int(offset.total_seconds() // 60) if offset else 0
    except Exception:
        active_tz_offset_minutes = 0

    return render(
        request,
        "opcalendar/event-add.html",
        {
            "form": form,
            "active_tz": active_tz_name,
            "active_tz_offset": active_tz_offset,
            "active_tz_offset_minutes": active_tz_offset_minutes,
        },
    )


def get_category(request):
    catecoty_id = request.GET.get("category", None)

    data = {
        "category": serializers.serialize(
            "json", EventCategory.objects.all().filter(id=catecoty_id)
        )
    }
    return JsonResponse(data)


@login_required
@permission_required("opcalendar.basic_access")
def event_details(request, event_id):
    try:
        # Get the event considering group and state visibility restrictions
        event = (
            Event.objects.filter(
                Q(event_visibility__restricted_to_group__in=request.user.groups.all())
                | Q(event_visibility__restricted_to_group__isnull=True),
            )
            .filter(
                Q(event_visibility__restricted_to_state=request.user.profile.state)
                | Q(event_visibility__restricted_to_state__isnull=True),
            )
            .get(id=event_id)
        )

        # Filter and order the event members by status and character name
        eventmember = EventMember.objects.filter(event=event).order_by(
            "status", "character__character_name"
        )

        # Create a list of character names (sorted by status and name)
        memberlist = [member.character.character_name for member in eventmember]

        # Active TZ banner data
        try:
            user_settings = UserSettings.objects.get(user=request.user)
            tz_name = user_settings.timezone or "UTC"
        except UserSettings.DoesNotExist:
            tz_name = "UTC"
        try:
            now_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
            offset = now_utc.astimezone(ZoneInfo(tz_name)).utcoffset()
            if offset is not None:
                total_minutes = int(offset.total_seconds() // 60)
                sign = "+" if total_minutes >= 0 else "-"
                abs_minutes = abs(total_minutes)
                hours = abs_minutes // 60
                minutes = abs_minutes % 60
                tz_offset = f"UTC{sign}{hours:02d}:{minutes:02d}"
                tz_offset_minutes = total_minutes
            else:
                tz_offset = "UTC±00:00"
                tz_offset_minutes = 0
        except Exception:
            tz_offset = "UTC±00:00"
            tz_offset_minutes = 0

        event_url = request.build_absolute_uri(event.get_absolute_url())

        context = {
            "event": event,
            "eventmember": eventmember,
            "memberlist": memberlist,
            "active_tz": tz_name,
            "active_tz_offset": tz_offset,
            "active_tz_offset_minutes": tz_offset_minutes,
            "event_url": event_url,
        }

        return render(request, "opcalendar/event-details.html", context)

    except Event.DoesNotExist:
        return redirect("opcalendar:calendar")


@login_required
@permission_required("opcalendar.create_event")
def EventEdit(request, event_id):
    logger.debug(
        "edit_event called by user %s for optimer id %s" % (request.user, event_id)
    )
    event = get_object_or_404(Event, id=event_id)

    # Determine user's active timezone (defaults to UTC)
    try:
        user_settings = UserSettings.objects.get(user=request.user)
        active_tz_name = user_settings.timezone or "UTC"
    except UserSettings.DoesNotExist:
        active_tz_name = "UTC"
    active_tz = ZoneInfo(active_tz_name)

    if request.method == "POST":
        form = EventEditForm(request.POST)
        logger.debug(
            "Received POST request containing update optimer form, is valid: %s"
            % form.is_valid()
        )
        if form.is_valid():
            # Update fields manually to convert local naive to UTC-aware
            event.operation_type = form.cleaned_data["operation_type"]
            event.title = form.cleaned_data["title"]
            event.host = form.cleaned_data["host"]
            event.doctrine = form.cleaned_data["doctrine"]
            event.formup_system = form.cleaned_data["formup_system"]
            event.description = form.cleaned_data["description"]
            start_time_local = form.cleaned_data["start_time"]
            end_time_local = form.cleaned_data["end_time"]

            # Check time_mode toggle: "eve" means times are already in UTC
            time_mode = request.POST.get("time_mode", "local")

            if time_mode == "eve":
                event.start_time = start_time_local.replace(tzinfo=timezone.utc)
                event.end_time = end_time_local.replace(tzinfo=timezone.utc)
            else:
                event.start_time = start_time_local.replace(tzinfo=active_tz).astimezone(timezone.utc)
                event.end_time = end_time_local.replace(tzinfo=active_tz).astimezone(timezone.utc)
            event.fc = form.cleaned_data["fc"]
            event.event_visibility = form.cleaned_data["event_visibility"]

            event.save()

            logger.info("User %s updating optimer id %s " % (request.user, event_id))

            messages.success(
                request,
                _("Saved changes to event for %(event)s.") % {"event": event.title},
            )
            url = reverse("opcalendar:event-detail", kwargs={"event_id": event.id})
            return HttpResponseRedirect(url)
    else:
        # When showing existing values, convert stored UTC to user's local tz for initial display
        initial = {
            "start_time": event.start_time.astimezone(ZoneInfo(active_tz_name)).replace(tzinfo=None),
            "end_time": event.end_time.astimezone(ZoneInfo(active_tz_name)).replace(tzinfo=None),
        }
        form = EventEditForm(instance=event, initial=initial)

    # Build an offset label like UTC+02:00
    try:
        now_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
        offset = now_utc.astimezone(active_tz).utcoffset()
        if offset is not None:
            total_minutes = int(offset.total_seconds() // 60)
            sign = "+" if total_minutes >= 0 else "-"
            total_minutes = abs(total_minutes)
            hours = total_minutes // 60
            minutes = total_minutes % 60
            active_tz_offset = f"UTC{sign}{hours:02d}:{minutes:02d}"
        else:
            active_tz_offset = "UTC±00:00"
    except Exception:
        active_tz_offset = None

    # Compute numeric offset in minutes for JS timezone conversion
    try:
        now_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
        offset = now_utc.astimezone(active_tz).utcoffset()
        active_tz_offset_minutes = int(offset.total_seconds() // 60) if offset else 0
    except Exception:
        active_tz_offset_minutes = 0

    return render(
        request,
        "opcalendar/event-edit.html",
        context={
            "form": form,
            "active_tz": active_tz_name,
            "active_tz_offset": active_tz_offset,
            "active_tz_offset_minutes": active_tz_offset_minutes,
        },
    )


@login_required
@permission_required("opcalendar.basic_access")
def ingame_event_details(request, event_id):
    event = IngameEvents.objects.get(event_id=event_id)

    # Active TZ banner data
    try:
        user_settings = UserSettings.objects.get(user=request.user)
        tz_name = user_settings.timezone or "UTC"
    except UserSettings.DoesNotExist:
        tz_name = "UTC"
    try:
        now_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
        offset = now_utc.astimezone(ZoneInfo(tz_name)).utcoffset()
        if offset is not None:
            total_minutes = int(offset.total_seconds() // 60)
            sign = "+" if total_minutes >= 0 else "-"
            total_minutes = abs(total_minutes)
            hours = total_minutes // 60
            minutes = total_minutes % 60
            tz_offset = f"UTC{sign}{hours:02d}:{minutes:02d}"
        else:
            tz_offset = "UTC±00:00"
    except Exception:
        tz_offset = "UTC±00:00"

    context = {"event": event, "active_tz": tz_name, "active_tz_offset": tz_offset}

    if request.user.has_perm("opcalendar.view_ingame"):
        return render(request, "opcalendar/ingame-event-details.html", context)
    else:
        return redirect("opcalendar:calendar")


@login_required
@permission_required("opcalendar.create_event")
def EventDeleteView(request, event_id):
    logger.debug(
        "remove_optimer called by user %s for operation id %s"
        % (request.user, event_id)
    )
    op = get_object_or_404(Event, id=event_id)
    op.delete()
    logger.info("Deleting optimer id %s by user %s" % (event_id, request.user))
    messages.error(request, _("Removed event %(opname)s.") % {"opname": op.title})
    return redirect("opcalendar:calendar")


@login_required
@permission_required("opcalendar.basic_access")
def EventMemberSignup(request, event_id):
    event = Event.objects.get(id=event_id)

    character = request.user.profile.main_character

    EventMember.objects.update_or_create(event=event, character=character)

    messages.success(
        request,
        _("Succesfully signed up for event: %(event)s with %(character)s.")
        % {"event": event, "character": character},
    )

    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


@login_required
@permission_required("opcalendar.basic_access")
def EventMemberRemove(request, event_id):
    event = Event.objects.get(id=event_id)

    character = request.user.profile.main_character

    eventmember = EventMember.objects.filter(event=event, character=character)

    eventmember.delete()

    messages.error(
        request,
        _("Removed signup for event: %(event)s for %(character)s.")
        % {"event": event, "character": character},
    )

    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


class EventFeed(ICalFeed):
    """
    A simple event calender
    """

    product_id = "-//{}//Opcalendar//FEED".format(get_site_url())
    timezone = "UTC"
    file_name = "event.ics"

    def items(self):
        return (
            Event.objects.all()
            .order_by("-start_time")
            .filter(event_visibility__include_in_feed=True)
        )

    def item_guid(self, item):
        return "{}{}".format(item.id, "global_name")

    def item_title(self, item):
        return "{}".format(item.title)

    def item_description(self, item):
        return item.description

    def item_class(self, item):
        return item.title

    def item_location(self, item):
        return item.formup_system

    def item_start_datetime(self, item):
        return item.start_time

    def item_end_datetime(self, item):
        return item.end_time

    def item_organizer(self, item):
        return item.fc

    def item_link(self, item):
        return "{0}/opcalendar/event/{1}/details/".format(get_site_url(), item.id)


class EventIcalView(ICalFeed):
    """
    A simple event calender
    """

    product_id = "-//{}//Opcalendar//FEED".format(get_site_url())
    timezone = "UTC"
    file_name = "event.ics"

    def __call__(self, request, event_id, *args, **kwargs):
        self.request = request
        self.event_id = event_id
        return super(EventIcalView, self).__call__(request, event_id, *args, **kwargs)

    def items(self, event_id):
        return (
            Event.objects.all()
            .filter(id=self.event_id)
            .filter(
                Q(
                    event_visibility__restricted_to_group__in=self.request.user.groups.all()
                )
                | Q(event_visibility__restricted_to_group__isnull=True),
            )
            .filter(
                Q(event_visibility__restricted_to_state=self.request.user.profile.state)
                | Q(event_visibility__restricted_to_state__isnull=True),
            )
        )

    def item_guid(self, item):
        return "{}{}".format(item.id, "global_name")

    def item_title(self, item):
        return "{}".format(item.title)

    def item_description(self, item):
        return item.description

    def item_class(self, item):
        return item.title

    def item_location(self, item):
        return item.formup_system

    def item_start_datetime(self, item):
        return item.start_time

    def item_end_datetime(self, item):
        return item.end_time

    def item_organizer(self, item):
        return item.host

    def item_link(self, item):
        return "{0}/opcalendar/event/{1}/details/".format(get_site_url(), item.id)


@login_required
def user_settings_view(request):
    try:
        user_settings = UserSettings.objects.get(user=request.user)
    except UserSettings.DoesNotExist:
        user_settings = UserSettings(user=request.user)

    if request.method == "POST":
        form = UserSettingsForm(request.POST, instance=user_settings)
        if form.is_valid():
            form.save()
            messages.success(request, "Your settings have been updated successfully.")
            return redirect("opcalendar:calendar")  # Redirect to the calendar page
        else:
            messages.error(
                request, "There was an error updating your settings. Please try again."
            )
    else:
        form = UserSettingsForm(instance=user_settings)

    # Active TZ banner data
    try:
        tz_name = user_settings.timezone or "UTC"
    except Exception:
        tz_name = "UTC"
    try:
        now_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
        offset = now_utc.astimezone(ZoneInfo(tz_name)).utcoffset()
        if offset is not None:
            total_minutes = int(offset.total_seconds() // 60)
            sign = "+" if total_minutes >= 0 else "-"
            total_minutes = abs(total_minutes)
            hours = total_minutes // 60
            minutes = total_minutes % 60
            tz_offset = f"UTC{sign}{hours:02d}:{minutes:02d}"
        else:
            tz_offset = "UTC±00:00"
    except Exception:
        tz_offset = "UTC±00:00"

    return render(
        request,
        "opcalendar/user_settings.html",
        {"form": form, "active_tz": tz_name, "active_tz_offset": tz_offset},
    )
