# Cog Stuff
from discord.ext import commands
from discord.embeds import Embed
from discord.colour import Color
# AA Contexts
from aadiscordbot.app_settings import get_site_url, get_admins
from allianceauth.services.modules.discord.models import DiscordUser

## OPCALENDAR
import operator
from opcalendar.models import Event, IngameEvents
from opcalendar.calendar import Calendar
from django.db.models import Q, F
from django.contrib.auth.models import User
from allianceauth.services.modules.discord.models import DiscordUser
from itertools import chain
from dateutil.relativedelta import relativedelta

import re
import logging
import pendulum
import traceback
logger = logging.getLogger(__name__)


class Ops(commands.Cog):
    """
    A Collection of Authentication Tools for Alliance Auth
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def ops(self, ctx):
        """
        Returns a link to the AllianceAuth Install
        Used by many other Bots and is a common command that users will attempt to run.
        """
        await ctx.trigger_typing()
        
        # Get authod ID
        id = ctx.message.author.id

        # Get user if discord service is active
        try:
            discord_user = DiscordUser.objects.get(uid=id)
            user = discord_user.user
        except Exception as e:
            logger.error("Discord service is not active for user")  

        # Get normal events
        # Filter by groups and states
        events = (
            Event.objects.filter(
                Q(event_visibility__restricted_to_group__in=user.groups.all())
                | Q(event_visibility__restricted_to_group__isnull=True),
            )
            .filter(
                Q(event_visibility__restricted_to_state=user.profile.state)
                | Q(event_visibility__restricted_to_state__isnull=True),
            )
        )
        # Get ingame events
        # Filter by groups and states
        ingame_events = (
            IngameEvents.objects.annotate(start_time=F("event_start_date"), end_time=F("event_end_date"))
            .filter(
                Q(
                    owner__event_visibility__restricted_to_group__in=user.groups.all()
                )
                | Q(owner__event_visibility__restricted_to_group__isnull=True),
            )
            .filter(
                Q(owner__event_visibility__restricted_to_state=user.profile.state)
                | Q(owner__event_visibility__restricted_to_state__isnull=True),
            )
        )

        # Combine events
        all_events = sorted(
            chain(events, ingame_events),
            key=operator.attrgetter("start_time"),
        )[:20]

        url = get_site_url()

        embed = Embed(title="Scheduled Opcalendar Events")
        
        embed.set_thumbnail(
            url="https://assets.gitlab-static.net/uploads/-/system/project/avatar/6840712/Alliance_auth.png?width=128"
        )
        embed.colour = Color.blue()

        embed.description = ("Here is the list of the next 20 upcoming operations. A calendar view is located in [here](%s/opcalendar)" % url)


        # Format all events and ingame events
        for event in all_events:
            if type(event) == Event:
                embed.add_field(
                    name="Event: {0}".format(event.title), value="Host: {0}\nFC: {1}\nDoctrine: {2}\nLocation: {3}\nTime: {4}\n\n{5}\n".format(event.host, event.fc, event.doctrine, event.formup_system, event.start_time, event.description), inline=False
                )
            if type(event) == IngameEvents:
                embed.add_field(
                    name="Ingame Event: {0}".format( event.title), value="Host: {0}\n Time:{1}\n\n{2}".format(event.owner_name, event.start_time, event.text), inline=False
                )

        return await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Ops(bot))