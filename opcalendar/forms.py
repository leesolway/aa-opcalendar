from django.forms import ModelForm
from opcalendar.models import (
    Event,
    EventMember,
    EventCategory,
    EventHost,
    EventVisibility,
)
from django.forms.widgets import TextInput
from django import forms


class EventForm(ModelForm):
    class Meta:
        model = Event
        # datetime-local is a HTML5 input type, format to make date time show on fields
        exclude = ["user", "eve_character", "created_date", "external"]

    def __init__(self, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)
        # input_formats to parse HTML5 datetime-local input to datetime field
        self.fields["start_time"].input_formats = ("%Y-%m-%dT%H:%M",)
        self.fields["end_time"].input_formats = ("%Y-%m-%dT%H:%M",)
        self.fields["host"].queryset = EventHost.objects.filter(external=False)
        self.fields["event_visibility"].required = True


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
        fields = ["character"]


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
