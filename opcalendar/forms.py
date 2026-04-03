from allianceauth.services.hooks import get_extension_logger
from django import forms
from django.forms import ModelForm
from django.forms.widgets import TextInput
from django.utils.translation import gettext_lazy as _

from .helpers import get_tz_offset_string

from opcalendar.models import (
    Event,
    EventCategory,
    EventHost,
    EventMember,
    EventVisibility,
    UserSettings,
)

logger = get_extension_logger(__name__)


class BaseEventForm(ModelForm):
    """Shared date-field initialization for all event forms."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        date_format = "%Y-%m-%dT%H:%M"
        self.fields["start_time"].input_formats = (date_format,)
        self.fields["end_time"].input_formats = (date_format,)
        self.fields["start_time"].widget.attrs.update({"autocomplete": "off"})
        self.fields["end_time"].widget.attrs.update({"autocomplete": "off"})


class EventForm(BaseEventForm):
    class Meta:
        model = Event
        exclude = ["user", "eve_character", "created_date", "external", "is_cancelled", "cancellation_reason", "is_placeholder"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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


class EventEditForm(BaseEventForm):
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
        super().__init__(*args, **kwargs)

        # Setup querysets and requirements for other fields
        self.fields["host"].queryset = EventHost.objects.filter(external=False)
        self.fields["event_visibility"].required = True
        self.fields["event_visibility"].queryset = EventVisibility.objects.filter(
            is_visible=True, is_active=True
        )


class PlaceholderEventForm(BaseEventForm):
    class Meta:
        model = Event
        fields = ["title", "event_visibility", "start_time", "end_time"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["event_visibility"].required = True
        self.fields["event_visibility"].queryset = EventVisibility.objects.filter(
            is_visible=True, is_active=True
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
    from zoneinfo import available_timezones

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
                label = f"{tz} ({get_tz_offset_string(tz)})"
            choices.append((tz, label))
        return choices
except Exception:  # pragma: no cover
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
                label = f"{tz} ({get_tz_offset_string(tz)})"
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
