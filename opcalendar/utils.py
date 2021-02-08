import socket
from calendar import HTMLCalendar
from datetime import datetime, date, timezone, timedelta
import random
import string
from typing import Any

from django.contrib import messages
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.messages.constants import DEBUG, ERROR, INFO, SUCCESS, WARNING
from django.test import TestCase
from django.utils.html import format_html

from esi.models import Scope, Token

from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import EveCharacter
from allianceauth.services.hooks import get_extension_logger
from allianceauth.tests.auth_utils import AuthUtils

from .models import Event, IngameEvents

logger = get_extension_logger(__name__)


class Calendar(HTMLCalendar):
    def __init__(self, year=None, month=None, user=None):
        self.year = year
        self.month = month
        self.user = user
        super(Calendar, self).__init__()

    # formats a day as a td
    # filter events by day
    def formatday(self, day, events, ingame_events):
        events_per_day = events.filter(start_time__day=day).order_by("start_time")
        ingame_events_per_day = ingame_events.filter(
            event_start_date__day=day
        ).order_by("event_start_date")
        d = ""

        # Only events for current month
        if day != 0:
            # Parse events
            for event in events_per_day:
                # Display public events
                if (
                    event.visibility == "public"
                    or event.visibility == "import"
                    and self.user.has_perm("opcalendar.view_public")
                ):
                    # Get past events
                    if datetime.now(timezone.utc) > event.start_time:
                        d += (
                            f'<a class="nostyling" href="{event.get_html_url}">'
                            f'<div class="event {event.get_html_operation_color} past-event {event.visibility}-event">{event.get_html_title}</div>'
                            f"</a>"
                        )
                    if datetime.now(timezone.utc) <= event.start_time:
                        d += (
                            f'<a class="nostyling" href="{event.get_html_url}">'
                            f'<div class="event {event.get_html_operation_color} {event.visibility}-event">{event.get_html_title}</div>'
                            f"</a>"
                        )
                if event.visibility == "member" and self.user.has_perm(
                    "opcalendar.view_member"
                ):
                    # Get past events
                    if datetime.now(timezone.utc) > event.start_time:
                        d += (
                            f'<a class="nostyling" href="{event.get_html_url}">'
                            f'<div class="event {event.get_html_operation_color} past-event {event.visibility}-event">{event.get_html_title}</div>'
                            f"</a>"
                        )
                    if datetime.now(timezone.utc) <= event.start_time:
                        d += (
                            f'<a class="nostyling" href="{event.get_html_url}">'
                            f'<div class="event {event.get_html_operation_color} {event.visibility}-event">{event.get_html_title}</div>'
                            f"</a>"
                        )
            for event in ingame_events_per_day:
                if self.user.has_perm("opcalendar.view_ingame"):
                    # Get past events
                    if datetime.now(timezone.utc) > event.event_start_date:
                        d += (
                            f'<a class="nostyling" href="{event.get_html_url}">'
                            f'<div class="event {event.get_html_operation_color} past-event import-event">{event.get_html_title}</div>'
                            f"</a>"
                        )
                    if datetime.now(timezone.utc) <= event.event_start_date:
                        d += (
                            f'<a class="nostyling" href="{event.get_html_url}">'
                            f'<div class="event {event.get_html_operation_color} import-event">{event.get_html_title}</div>'
                            f"</a>"
                        )

            if date.today() == date(self.year, self.month, day):
                return f"<td class='today'><div class='date'>{day}</div> {d}</td>"
            return f"<td><div class='date'>{day}</div> {d}</td>"
        return "<td></td>"

    # formats a week as a tr
    def formatweek(self, theweek, events, ingame_events):
        week = ""
        for d, weekday in theweek:
            week += self.formatday(d, events, ingame_events)
        return f"<tr> {week} </tr>"

    # formats a month as a table
    # filter events by year and month
    def formatmonth(self, withyear=True):
        events = Event.objects.filter(
            start_time__year=self.year, start_time__month=self.month
        )
        ingame_events = IngameEvents.objects.filter(
            event_start_date__year=self.year, event_start_date__month=self.month
        )

        cal = '<table class="calendar">\n'
        cal += f"{self.formatmonthname(self.year, self.month, withyear=withyear)}\n"
        cal += f"{self.formatweekheader()}\n"

        for week in self.monthdays2calendar(self.year, self.month):
            cal += f"{self.formatweek(week, events, ingame_events)}\n"

        cal += "</table>"

        return cal


def clean_setting(
    name: str,
    default_value: object,
    min_value: int = None,
    max_value: int = None,
    required_type: type = None,
    choices: list = None,
) -> Any:
    """cleans the input for a custom setting

    Will use `default_value` if settings does not exit or has the wrong type
    or is outside define boundaries (for int only)

    Need to define `required_type` if `default_value` is `None`

    Will assume `min_value` of 0 for int (can be overriden)

    `None` allowed as value

    Returns cleaned value for setting
    """
    if default_value is None and not required_type:
        raise ValueError("You must specify a required_type for None defaults")

    if not required_type:
        required_type = type(default_value)

    if min_value is None and required_type == int:
        min_value = 0

    if not hasattr(settings, name):
        cleaned_value = default_value
    else:
        dirty_value = getattr(settings, name)
        if dirty_value is None or (
            isinstance(dirty_value, required_type)
            and (min_value is None or dirty_value >= min_value)
            and (max_value is None or dirty_value <= max_value)
            and (choices is None or dirty_value in choices)
        ):
            cleaned_value = dirty_value
        else:
            logger.warn(
                "You setting for {} it not valid. Please correct it. "
                "Using default for now: {}".format(name, default_value)
            )
            cleaned_value = default_value
    return cleaned_value


class messages_plus:
    """Pendant to Django messages adding level icons and HTML support

    Careful: Use with safe strings only
    """

    _glyph_map = {
        DEBUG: "eye-open",
        INFO: "info-sign",
        SUCCESS: "ok-sign",
        WARNING: "exclamation-sign",
        ERROR: "alert",
    }

    @classmethod
    def _add_messages_icon(cls, level: int, message: str) -> str:
        """Adds an level based icon to standard Django messages"""
        if level not in cls._glyph_map:
            raise ValueError("glyph for level not defined")
        else:
            glyph = cls._glyph_map[level]

        return format_html(
            '<span class="glyphicon glyphicon-{}" '
            'aria-hidden="true"></span>&nbsp;&nbsp;{}',
            glyph,
            message,
        )

    @classmethod
    def debug(
        cls,
        request: object,
        message: str,
        extra_tags: str = "",
        fail_silently: bool = False,
    ):
        messages.debug(
            request, cls._add_messages_icon(DEBUG, message), extra_tags, fail_silently
        )

    @classmethod
    def info(
        cls,
        request: object,
        message: str,
        extra_tags: str = "",
        fail_silently: bool = False,
    ):
        messages.info(
            request, cls._add_messages_icon(INFO, message), extra_tags, fail_silently
        )

    @classmethod
    def success(
        cls,
        request: object,
        message: str,
        extra_tags: str = "",
        fail_silently: bool = False,
    ):
        messages.success(
            request, cls._add_messages_icon(SUCCESS, message), extra_tags, fail_silently
        )

    @classmethod
    def warning(
        cls,
        request: object,
        message: str,
        extra_tags: str = "",
        fail_silently: bool = False,
    ):
        messages.warning(
            request, cls._add_messages_icon(WARNING, message), extra_tags, fail_silently
        )

    @classmethod
    def error(
        cls,
        request: object,
        message: str,
        extra_tags: str = "",
        fail_silently: bool = False,
    ):
        messages.error(
            request, cls._add_messages_icon(ERROR, message), extra_tags, fail_silently
        )


class SocketAccessError(Exception):
    pass


class NoSocketsTestCase(TestCase):
    """Variation of TestCase class that prevents any use of sockets"""

    @classmethod
    def setUpClass(cls):
        cls.socket_original = socket.socket
        socket.socket = cls.guard
        return super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        socket.socket = cls.socket_original
        return super().tearDownClass()

    @staticmethod
    def guard(*args, **kwargs):
        raise SocketAccessError("Attempted to access network")


class BravadoResponseStub:
    """Stub for IncomingResponse in bravado, e.g. for HTTPError exceptions"""

    def __init__(
        self, status_code, reason="", text="", headers=None, raw_bytes=None
    ) -> None:
        self.reason = reason
        self.status_code = status_code
        self.text = text
        self.headers = headers if headers else dict()
        self.raw_bytes = raw_bytes

    def __str__(self):
        return "{0} {1}".format(self.status_code, self.reason)


class BravadoOperationStub:
    """Stub to simulate the operation object return from bravado via django-esi"""

    class RequestConfig:
        def __init__(self, also_return_response):
            self.also_return_response = also_return_response

    class ResponseStub:
        def __init__(self, headers):
            self.headers = headers

    def __init__(self, data, headers: dict = None, also_return_response: bool = False):
        self._data = data
        self._headers = headers if headers else {"x-pages": 1}
        self.request_config = BravadoOperationStub.RequestConfig(also_return_response)

    def result(self, **kwargs):
        if self.request_config.also_return_response:
            return [self._data, self.ResponseStub(self._headers)]
        else:
            return self._data

    def results(self, **kwargs):
        return self.result(**kwargs)


def add_character_to_user(
    user: User,
    character: EveCharacter,
    is_main: bool = False,
    scopes: list = None,
) -> CharacterOwnership:
    if not scopes:
        scopes = "publicData"

    add_new_token(user, character, scopes)

    if is_main:
        user.profile.main_character = character
        user.profile.save()
        user.save()

    return CharacterOwnership.objects.get(user=user, character=character)


def add_character_to_user_2(
    user: User,
    character_id,
    character_name,
    corporation_id,
    corporation_name,
    alliance_id=None,
    alliance_name=None,
    disconnect_signals=False,
) -> EveCharacter:
    defaults = {
        "character_name": str(character_name),
        "corporation_id": int(corporation_id),
        "corporation_name": str(corporation_name),
    }
    if alliance_id:
        defaults["alliance_id"] = int(alliance_id)
        defaults["alliance_name"] = str(alliance_name)

    if disconnect_signals:
        AuthUtils.disconnect_signals()
    character, _ = EveCharacter.objects.update_or_create(
        character_id=character_id, defaults=defaults
    )
    CharacterOwnership.objects.create(
        character=character, owner_hash=f"{character_id}_{character_name}", user=user
    )
    if disconnect_signals:
        AuthUtils.connect_signals()

    return character


def add_new_token(user: User, character: EveCharacter, scopes: list) -> Token:
    """generates a new Token for the given character and adds it to the user"""
    return _store_as_Token(
        _generate_token(
            character_id=character.character_id,
            character_name=character.character_name,
            scopes=scopes,
        ),
        user,
    )


def _generate_token(
    character_id: int,
    character_name: str,
    access_token: str = "access_token",
    refresh_token: str = "refresh_token",
    scopes: list = None,
    timestamp_dt: object = None,
    expires_in: int = 1200,
) -> dict:

    if timestamp_dt is None:
        timestamp_dt = datetime.utcnow()
    if scopes is None:
        scopes = [
            "esi-mail.read_mail.v1",
            "esi-wallet.read_character_wallet.v1",
            "esi-universe.read_structures.v1",
        ]
    token = {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": expires_in,
        "refresh_token": refresh_token,
        "timestamp": int(timestamp_dt.timestamp()),
        "CharacterID": character_id,
        "CharacterName": character_name,
        "ExpiresOn": _dt_eveformat(timestamp_dt + timedelta(seconds=expires_in)),
        "Scopes": " ".join(list(scopes)),
        "TokenType": "Character",
        "CharacterOwnerHash": _get_random_string(28),
        "IntellectualProperty": "EVE",
    }
    return token


def _dt_eveformat(dt: object) -> str:
    """converts a datetime to a string in eve format
    e.g. '2019-06-25T19:04:44'
    """
    dt2 = datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    return dt2.isoformat()


def _get_random_string(char_count):
    return "".join(
        random.choice(string.ascii_uppercase + string.digits) for _ in range(char_count)
    )


def _store_as_Token(token: dict, user: object) -> object:
    """Stores a generated token dict as Token object for given user

    returns Token object
    """
    obj = Token.objects.create(
        access_token=token["access_token"],
        refresh_token=token["refresh_token"],
        user=user,
        character_id=token["CharacterID"],
        character_name=token["CharacterName"],
        token_type=token["TokenType"],
        character_owner_hash=token["CharacterOwnerHash"],
    )
    for scope_name in token["Scopes"].split(" "):
        scope, _ = Scope.objects.get_or_create(name=scope_name)
        obj.scopes.add(scope)

    return obj
