from allianceauth.services.hooks import get_extension_logger
from django import forms
from django.forms import ModelForm
from django.forms.widgets import TextInput

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
        exclude = ["user", "eve_character", "created_date", "external"]

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


class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = UserSettings
        fields = ["disable_discord_notifications", "use_local_times"]
        labels = {
            "disable_discord_notifications": "Disable all direct discord notifications",
            "use_local_times": "Show all events in local time instead of EVE time",
        }
