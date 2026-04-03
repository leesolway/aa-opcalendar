from allianceauth.services.hooks import get_extension_logger
from django import forms
from django.forms import ModelForm
from django.forms.widgets import TextInput
from django.utils.translation import gettext_lazy as _

from opcalendar.models import (
    Event,
    EventCategory,
    EventHost,
    EventMember,
    EventVisibility,
    UserSettings,
)

logger = get_extension_logger(__name__)


class EventForm(ModelForm):
    class Meta:
        model = Event
        exclude = ["user", "eve_character", "created_date", "external", "is_cancelled", "cancellation_reason", "is_placeholder"]

    def __init__(self, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)

        # Define the date format
        date_format = "%Y-%m-%dT%H:%M"
        self.fields["start_time"].input_formats = (date_format,)
        self.fields["end_time"].input_formats = (date_format,)

        # Set autocomplete attribute to "off" for date fields
        self.fields["start_time"].widget.attrs.update({"autocomplete": "off"})
        self.fields["end_time"].widget.attrs.update({"autocomplete": "off"})

        # Setup querysets and requirements for other fields
        self.fields["host"].queryset = EventHost.objects.filter(external=False)
        self.fields["event_visibility"].required = True
        self.fields["event_visibility"].queryset = EventVisibility.objects.filter(
            is_visible=True, is_active=True
        )

        # Setting default values for event_visibility and host
        try:
            self.initial["event_visibility"] = EventVisibility.objects.get(
                is_default=True
            )
        except EventVisibility.DoesNotExist:
            logger.debug("Form defaults: No default visibility set")

        try:
            self.initial["host"] = EventHost.objects.get(is_default=True)
        except EventHost.DoesNotExist:
            logger.debug("Form defaults: No default host set")


class EventEditForm(ModelForm):
    class Meta:
        model = Event
        exclude = [
            "user",
            "eve_character",
            "created_date",
            "external",
            "repeat_event",
            "repeat_times",
            "is_cancelled",
            "cancellation_reason",
            "is_placeholder",
        ]

    def __init__(self, *args, **kwargs):
        super(EventEditForm, self).__init__(*args, **kwargs)

        # Define the date format
        date_format = "%Y-%m-%dT%H:%M"
        self.fields["start_time"].input_formats = (date_format,)
        self.fields["end_time"].input_formats = (date_format,)

        # Set autocomplete attribute to "off" for date fields
        self.fields["start_time"].widget.attrs.update({"autocomplete": "off"})
        self.fields["end_time"].widget.attrs.update({"autocomplete": "off"})

        # Setup querysets and requirements for other fields
        self.fields["host"].queryset = EventHost.objects.filter(external=False)
        self.fields["event_visibility"].required = True
        self.fields["event_visibility"].queryset = EventVisibility.objects.filter(
            is_visible=True, is_active=True
        )


class PlaceholderEventForm(ModelForm):
    class Meta:
        model = Event
        fields = ["title", "event_visibility", "start_time", "end_time"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        date_format = "%Y-%m-%dT%H:%M"
        self.fields["start_time"].input_formats = (date_format,)
        self.fields["end_time"].input_formats = (date_format,)
        self.fields["start_time"].widget.attrs.update({"autocomplete": "off"})
        self.fields["end_time"].widget.attrs.update({"autocomplete": "off"})
        self.fields["event_visibility"].required = True
        self.fields["event_visibility"].queryset = EventVisibility.objects.filter(
            is_visible=True, is_active=True
        )


class SignupForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Username"}
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Password"}
        )
    )


class AddMemberForm(forms.ModelForm):
    class Meta:
        model = EventMember
        fields = ["character", "status", "comment"]
        widgets = {
            "comment": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "maxlength": 100,
                    "placeholder": "Optional comment",
                }
            ),
        }


class AddCategoryForm(forms.ModelForm):
    class Meta:
        model = EventCategory
        fields = "__all__"


class EventVisibilityAdminForm(forms.ModelForm):
    class Meta:
        model = EventVisibility
        fields = "__all__"
        widgets = {
            "color": TextInput(attrs={"type": "color"}),
        }


class EventCategoryAdminForm(forms.ModelForm):
    class Meta:
        model = EventCategory
        fields = "__all__"
        widgets = {
            "color": TextInput(attrs={"type": "color"}),
        }


# Helper to build timezone choices for a dropdown, with offsets in labels
try:
    from zoneinfo import ZoneInfo, available_timezones
    from datetime import datetime, timezone as dt_timezone

    def _fmt_offset(tzname: str) -> str:
        now_utc = datetime.now(dt_timezone.utc)
        try:
            offset = now_utc.astimezone(ZoneInfo(tzname)).utcoffset()
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

    def get_timezone_choices():
        tzs = sorted(
            [tz for tz in available_timezones() if "/" in tz and not tz.startswith("Etc/")]
        )
        # Put UTC at the top
        tzs = ["UTC"] + [t for t in tzs if t != "UTC"]
        choices = []
        for tz in tzs:
            if tz == "UTC":
                label = "UTC - EVE Time"
            else:
                label = f"{tz} ({_fmt_offset(tz)})"
            choices.append((tz, label))
        return choices
except Exception:  # pragma: no cover
    from datetime import datetime, timezone as dt_timezone
    try:
        from zoneinfo import ZoneInfo
    except Exception:
        ZoneInfo = None  # type: ignore

    def _fmt_offset_fallback(tzname: str) -> str:
        if not ZoneInfo:
            return "UTC±00:00"
        now_utc = datetime.now(dt_timezone.utc)
        try:
            offset = now_utc.astimezone(ZoneInfo(tzname)).utcoffset()
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

    def get_timezone_choices():
        fallback = [
            "UTC",
            "America/New_York",
            "America/Chicago",
            "America/Denver",
            "America/Los_Angeles",
            "Europe/London",
            "Europe/Berlin",
            "Australia/Sydney",
        ]
        choices = []
        for tz in fallback:
            if tz == "UTC":
                label = "UTC - EVE Time"
            else:
                label = f"{tz} ({_fmt_offset_fallback(tz)})"
            choices.append((tz, label))
        return choices


class CancelEventForm(forms.Form):
    cancellation_reason = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False,
        label=_("Cancellation reason"),
    )


class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = UserSettings
        fields = ["disable_discord_notifications", "timezone"]
        labels = {
            "disable_discord_notifications": "Disable all direct discord notifications",
            "timezone": "Preferred timezone",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["timezone"].widget = forms.Select(
            choices=get_timezone_choices(), attrs={"class": "form-select"}
        )
        # Harmonize label text with other fields
        self.fields["timezone"].label = "Timezone"
