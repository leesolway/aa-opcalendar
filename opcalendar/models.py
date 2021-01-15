import requests
import json

from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from allianceauth.eveonline.models import EveCharacter

from django.utils.translation import ugettext_lazy as _
# Create your models here.

class General(models.Model):
    """Meta model for app permissions"""

    class Meta:
        managed = False
        default_permissions = ()
        permissions = (
            ("basic_access", "Can access this app"),
            ("view_public", "Can see public events"),
            ("view_member", "Can see member events"),
            ("create_event", "Can create and edit events"),
            ("manage_event", "Can delete and manage signups"),
        )     

class WebHook(models.Model):
    """Discord Webhook for pings"""
    name = models.CharField(max_length=150)
    webhook_url = models.CharField(max_length=500)
    enabled = models.BooleanField()

    def send_embed(self, embed):
        custom_headers = {'Content-Type': 'application/json'}
        data = '{"embeds": [%s]}' % json.dumps(embed)
        r = requests.post(self.webhook_url, headers=custom_headers,
                            data=data)
        r.raise_for_status()

    class Meta:
        verbose_name = 'Webhook'
        verbose_name_plural = 'Webhooks'

    def __str__(self):
        return '{}'.format(self.name)

class EventSignal(models.Model):
    """Fleet Timer Create/Delete pings"""

    webhook = models.ForeignKey(WebHook, on_delete=models.CASCADE)

    ignore_past_fleets = models.BooleanField(default=True)

    def __str__(self):
        return 'Send Fleets to "{}"'.format(self.webhook.name)

    class Meta:
        verbose_name = 'Fleet Signal'
        verbose_name_plural = 'Fleet Signals'    

class EventHost(models.Model):
    """Fleet Timer Create/Delete pings"""

    community = models.CharField(max_length=150, null=False)
    ingame_channel = models.CharField(max_length=150, blank=True)
    ingame_mailing_list = models.CharField(max_length=150, blank=True)
    fleet_comms = models.CharField(max_length=150, blank=True)
    fleet_doctrines = models.CharField(max_length=150, blank=True)
    website = models.CharField(max_length=150, blank=True)
    discord = models.CharField(max_length=150, blank=True)
    twitch = models.CharField(max_length=150, blank=True)
    twitter = models.CharField(max_length=150, blank=True)
    youtube = models.CharField(max_length=150, blank=True)
    facebook = models.CharField(max_length=150, blank=True)
    details = models.CharField(max_length=150, blank=True)
   
    def __str__(self):
        return str(self.community)

    class Meta:
        verbose_name = 'Host'
        verbose_name_plural = 'Hosts'           

class EventCategory(models.Model):
    # Colors for calendar
    COLOR_BLUE = "blue"
    COLOR_GREEN = "green"
    COLOR_RED = "red"
    COLOR_ORANGE = "orange"  
    COLOR_GREY = "grey"
    COLOR_YELLOW = "yellow"
    COLOR_PURPLE = "purple"

    COLOR_CHOICES = (
        (COLOR_GREEN, _("Green")),
        (COLOR_RED, _("Red")),
        (COLOR_ORANGE, _("Orange")),
        (COLOR_BLUE, _("Blue")),
        (COLOR_GREY, _("Grey")),
        (COLOR_YELLOW, _("Yellow")),
        (COLOR_PURPLE, _("Purple")),

    )
    name = models.CharField(max_length=150)
    ticker = models.CharField(max_length=10) 
    color = models.CharField(max_length=6, choices=COLOR_CHOICES, default='green')

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    def __str__(self):
        return str(self.name)

class EventImport(models.Model):
    """NPSI IMPORT OPTIONS"""
    SPECTRE_FLEET = "Spectre Fleet"
    EVE_UNIVERSITY = "EVE University"
    
    IMPORT_SOURCES = (
        (SPECTRE_FLEET, _("Spectre Fleet")),
        (EVE_UNIVERSITY, _("EVE University")),
        )

    source = models.CharField(
        max_length=32,
        choices=IMPORT_SOURCES,
        help_text="The API source where you want to pull events from"
    )
    
    host = models.ForeignKey(
        EventHost, on_delete=models.CASCADE,
        default=1,
        help_text="The AA host that will be used for the pulled events"
    )
    operation_type = models.ForeignKey(
        EventCategory,
        on_delete=models.CASCADE,
        help_text="Operation type and ticker that will be assigned for the pulled fleets"
    )
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        default='1',
        help_text="User that has been used to create the fleet (most often the superuser who manages the plugin)"
    )
    eve_character = models.ForeignKey(
        EveCharacter,
        null=True,
        on_delete=models.SET_NULL,
        help_text="Event creator main character"
    )
   
    def __str__(self):
        return str(self.source)

    class Meta:
        verbose_name = 'Event Import'
        verbose_name_plural = 'Event Imports'   

class Event(models.Model):
    # visibility
    VISIBILITY_PUBLIC = "public"
    VISIBILITY_MEMBER = "member"
    VISIBILITY_EXTERNAL = "import"

    VISIBILITY_CHOICES = [
        (VISIBILITY_PUBLIC, _("Public access")),
        (VISIBILITY_MEMBER, _("Members only access")),
    ]


    operation_type = models.ForeignKey(
        EventCategory, 
        on_delete=models.CASCADE
    )
    title = models.CharField(
        max_length=200, 
        unique=False
    )
    host = models.ForeignKey(
        EventHost, 
        on_delete=models.CASCADE, 
        default=1
    )
    doctrine = models.CharField(
        max_length=254, 
        default="", 
        blank=True
    )
    formup_system = models.CharField(
        max_length=254, 
        default="", 
        blank=True
    )
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    fc = models.CharField(
        max_length=254, 
        default=""
    )
    visibility = models.CharField(
        max_length=7,
        choices=VISIBILITY_CHOICES,
        default=VISIBILITY_PUBLIC,
        db_index=True,
    )
    created_date = models.DateTimeField(
        default=timezone.now
    )
    eve_character = models.ForeignKey(
        EveCharacter,
        null=True,
        on_delete=models.SET_NULL
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ['title', 'start_time']

    def duration(self):
        return self.end_time - self.start_time

    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('opcalendar:event-detail', args=(self.id,))

    @property
    def get_html_url(self):
        url = reverse('opcalendar:event-detail', args=(self.id,))
        return f'{url}'

    @property
    def get_html_title(self):
        return f'{self.start_time.strftime("%H:%M")} - {self.end_time.strftime("%H:%M")} <i>{self.host.community}</i> <br> <b>{self.operation_type.ticker} {self.title}</b>'
    @property
    def get_html_operation_color(self):
        return f'{self.operation_type.color}'

    @property
    def get_html_visibility_color(self):
        if self.visibility=="public":
            return "purple"
        if self.visibility=="import":
            return "grey"
        if self.visibility=="member":   
            return "blue"

    def user_can_edit(self, user: user) -> bool:
        """Checks if the given user can edit this timer. Returns True or False"""
        return user.has_perm("opcalendar.manage_event") or (
            self.user == user and user.has_perm("opcalendar.create_event")
        )

class EventMember(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ['event', 'user']

    def __str__(self):
        return str(self.user)

    
