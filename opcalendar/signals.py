from django.dispatch import receiver

from django.db.models.signals import post_save, pre_delete, pre_save
from allianceauth.groupmanagement.models import GroupRequest
from allianceauth.authentication.models import UserProfile, CharacterOwnership, EveCharacter
from allianceauth.eveonline.evelinks.eveimageserver import  type_icon_url, character_portrait_url
from .models import Event, EventSignal
import requests
import json
import datetime
from django.utils import timezone

from .app_settings import get_site_url
from .helpers import time_helpers

from allianceauth.services.hooks import get_extension_logger
logger = get_extension_logger(__name__)

from django.utils.translation import ugettext_lazy as _

RED = 16711710
BLUE = 42751
GREEN = 6684416


@receiver(post_save, sender=Event)
def fleet_saved(sender, instance, created, **kwargs):
    if not "import" in instance.visibility:
        try:
            logger.debug("New signal fleet created for %s" % instance.title)
            url = get_site_url() + "/opcalendar/"
            main_char = instance.eve_character
            formup_system = instance.formup_system
            title = instance.title
            doctrine = instance.doctrine
            eve_time = instance.start_time
            fc = instance.fc
            col = GREEN
            message = "New Fleet Timer Posted"
            if not created:
                message = "Fleet Timer Updated"
                col = BLUE

            embed = {'title': message, 
                    'description': ("**{}** from **{}**".format(title,formup_system)),
                    'url': url,
                    'color': col,
                    "fields": [
                        {
                        "name": "FC",
                        "value": fc,
                        "inline": True
                        },
                        {
                        "name": "Doctrine",
                        "value": doctrine,
                        "inline": True
                        },
                        {
                        "name": "Eve Time",
                        "value": eve_time.strftime("%Y-%m-%d %H:%M:%S")
                        },
                        {
                        "name": "Time Until",
                        "value": time_helpers.get_time_until(eve_time)
                        }

                    ],
                    "footer": {
                        "icon_url": main_char.portrait_url_64,
                        "text": "{}  [{}]".format(main_char.character_name, main_char.corporation_ticker)
                    }
                }

            hooks = EventSignal.objects.all().select_related('webhook')
            logger.debug("Hooks OK ")
            old = datetime.datetime.now(timezone.utc) > eve_time
            logger.debug("Datetime OK")
            for hook in hooks:
                if hook.webhook.enabled:
                    if old and hook.ignore_past_fleets:
                        continue
            hook.webhook.send_embed(embed)

        except Exception as e:
            print(logger.error(e))
            pass  # shits fucked... Don't worry about it...

@receiver(pre_delete, sender=Event)
def fleet_deleted(sender, instance, **kwargs):
    if not "import" in instance.visibility:
        try:
            logger.debug("New signal fleet deleted for %s" % instance.title)
            url = get_site_url() + "/optimer/"
            main_char = instance.eve_character
            formup_system = instance.formup_system
            title = instance.title
            doctrine = instance.doctrine

            eve_time = instance.start_time

            fc = instance.fc
            message = "Fleet Removed"

            embed = {'title': message, 
                    'description': ("**{}** from **{}** has been cancelled".format(title,formup_system)),
                    'url': url,
                    'color': RED,
                    "fields": [
                        {
                        "name": "FC",
                        "value": fc,
                        "inline": True
                        },
                        {
                        "name": "Eve Time",
                        "value": eve_time.strftime("%Y-%m-%d %H:%M:%S")
                        }

                    ],
                    "footer": {
                        "icon_url": main_char.portrait_url_64,
                        "text": "{}  [{}]".format(main_char.character_name, main_char.corporation_ticker)
                    }
                }

            hooks = EventSignal.objects.all().select_related('webhook')
            old = datetime.datetime.now(timezone.utc) > eve_time

            for hook in hooks:
                if hook.webhook.enabled:
                    if old and hook.ignore_past_fleets:
                        continue
                    hook.webhook.send_embed(embed)

        except Exception as e:
            logger.error(e)
            pass  # shits fucked... Don't worry about it...