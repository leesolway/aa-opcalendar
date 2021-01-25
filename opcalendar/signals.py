from django.dispatch import receiver

from django.db.models.signals import post_save, pre_delete, pre_save
from allianceauth.groupmanagement.models import GroupRequest
from allianceauth.authentication.models import UserProfile, CharacterOwnership, EveCharacter
from allianceauth.eveonline.evelinks.eveimageserver import  type_icon_url, character_portrait_url
from .models import Event, EventSignal, IngameEvents
import requests
import json
import datetime
from django.utils import timezone

from esi.clients import EsiClientProvider

from .app_settings import get_site_url
from .helpers import time_helpers

from allianceauth.services.hooks import get_extension_logger
logger = get_extension_logger(__name__)

from django.utils.translation import ugettext_lazy as _

from .app_settings import (
    OPCALENDAR_NOTIFY_IMPORTS,
)

RED = 16711710
BLUE = 42751
GREEN = 6684416

esi = EsiClientProvider()

@receiver(post_save, sender=Event)
@receiver(post_save, sender=IngameEvents)
def fleet_saved(sender, instance, created, **kwargs):
     
    # Translate titles if we have ingame events
    if sender == IngameEvents:
        instance.visibility = ""

    if not "import" in instance.visibility or OPCALENDAR_NOTIFY_IMPORTS:
        try:
            logger.debug("New signal fleet created for %s" % instance.title)
            url = get_site_url() + "/optimer/"
            
            # Translate titles if we have ingame events
            if sender == IngameEvents:
                
                message = "New Event Created From API Feed"

                # Get the entity name from owner name
                entity_id = esi.client.Search.get_search(
                    categories=[instance.owner_type],
                    search=instance.owner_name, 
                    strict=True).results()[instance.owner_type][0]

                logger.debug("Entity data is %s" % entity_id)
                
                main_char = instance.owner.character.character.character_name
                
                formup_system = instance.owner_name
                
                title = instance.title
                
                doctrine = ""
                
                eve_time = instance.event_start_date
                
                fc = instance.owner_name
                
                # Setup portrait URL based on owner type
                if instance.owner_type == "alliance":
                    portrait = "https://images.evetech.net/alliances/{}/logo".format(entity_id)
                    ticker = "[{}]".format(esi.client.Alliance.get_alliances_alliance_id(
                        alliance_id = entity_id
                        ).results()["ticker"])

                if instance.owner_type == "corporation":
                    portrait = "https://images.evetech.net/corporations/{}/logo".format(entity_id)
                    ticker = "[{}]".format(esi.client.Corporation.get_corporations_corporation_id(
                        corporation_id = entity_id
                        ).results()["ticker"])

                if instance.owner_type == "character": 
                    portrait = "https://images.evetech.net/characters/{}/portrait".format(entity_id) 
                    ticker = ""

                logger.debug("Portrait url is %s" % portrait)

                character_name = instance.owner_name            

            else:

                message = "New Fleet Event "

                main_char = instance.eve_character
                
                formup_system = instance.formup_system
                
                title = instance.title
                
                doctrine = instance.doctrine
                
                eve_time = instance.start_time
                
                fc = instance.fc

                portrait = main_char.portrait_url_64

                character_name = main_char.character_name

                ticker = "{}".format(main_char.corporation_ticker)

            #If we update instead of delete
            if not created:
                message = "Event Updated"
                col = BLUE
            else:
                col = GREEN

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
                        "name": "Eve Time",
                        "value": eve_time.strftime("%Y-%m-%d %H:%M:%S")
                        }

                    ],
                    "footer": {
                        "icon_url": portrait,
                        "text": "{}  {}".format(character_name, ticker)
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

@receiver(pre_delete, sender=Event)
@receiver(pre_delete, sender=IngameEvents)
def fleet_deleted(sender, instance, **kwargs):
     
    # Translate titles if we have ingame events
    if sender == IngameEvents:
        instance.visibility = ""

    if not "import" in instance.visibility or OPCALENDAR_NOTIFY_IMPORTS:
        try:
            logger.debug("New signal fleet deleted for %s" % instance.title)
            url = get_site_url() + "/optimer/"
            
            # Translate titles if we have ingame events
            if sender == IngameEvents:
                
                message = "Event Removed Via API Feed"

                # Get the entity name from owner name
                entity_id = esi.client.Search.get_search(
                    categories=[instance.owner_type],
                    search=instance.owner_name, 
                    strict=True).results()[instance.owner_type][0]

                logger.debug("Entity data is %s" % entity_id)
                
                main_char = instance.owner.character.character.character_name
                
                formup_system = instance.owner_name
                
                title = instance.title
                
                doctrine = ""
                
                eve_time = instance.event_start_date
                
                fc = instance.owner_name
                
                # Setup portrait URL based on owner type
                if instance.owner_type == "alliance":
                    portrait = "https://images.evetech.net/alliances/{}/logo".format(entity_id)
                    ticker = "[{}]".format(esi.client.Alliance.get_alliances_alliance_id(
                        alliance_id = entity_id
                        ).results()["ticker"])

                if instance.owner_type == "corporation":
                    portrait = "https://images.evetech.net/corporations/{}/logo".format(entity_id)
                    ticker = "[{}]".format(esi.client.Corporation.get_corporations_corporation_id(
                        corporation_id = entity_id
                        ).results()["ticker"])

                if instance.owner_type == "character": 
                    portrait = "https://images.evetech.net/characters/{}/portrait".format(entity_id) 
                    ticker = ""

                logger.debug("Portrait url is %s" % portrait)

                character_name = instance.owner_name            

            else:

                message = "Fleet Event Removed"

                main_char = instance.eve_character
                
                formup_system = instance.formup_system
                
                title = instance.title
                
                doctrine = instance.doctrine
                
                eve_time = instance.start_time
                
                fc = instance.fc

                portrait = main_char.portrait_url_64

                character_name = main_char.character_name

                ticker = "{}".format(main_char.corporation_ticker)

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
                        "icon_url": portrait,
                        "text": "{}  {}".format(character_name, ticker)
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