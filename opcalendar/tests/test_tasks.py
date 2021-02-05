import datetime as dt
from unittest.mock import patch

from django.test import TestCase
from pytz import utc

from allianceauth.tests.auth_utils import AuthUtils

from ..models import Event, EventCategory, EventHost, EventImport
from .. import tasks
from .testdata import feedparser_parse


MODULE_PATH = "opcalendar.tasks"


class TestImportNpsiFleet(TestCase):
    @patch(MODULE_PATH + ".feedparser.parse", feedparser_parse)
    def test_should_add_new_fleets_from_scratch(self):
        # given
        # mock_feedparser_parse.sideeffect = feedparser_parse
        user = AuthUtils.create_user("Bruce Wayne")
        eve_character = AuthUtils.add_main_character_2(user, "Bruce Wayne", 1001, 2001)
        host = EventHost.objects.create(community="Test Host")
        category = EventCategory.objects.create(
            name="NPSI", ticker="NPSI", color=EventCategory.COLOR_PURPLE
        )
        EventImport.objects.create(
            source=EventImport.SPECTRE_FLEET,
            host=host,
            operation_type=category,
            creator=user,
            eve_character=eve_character,
        )
        # when
        tasks.import_all_npsi_fleets()
        # then
        self.assertEqual(Event.objects.count(), 1)
        obj = Event.objects.first()
        self.assertEqual(obj.operation_type, category)
        self.assertEqual(obj.title, "Spectre Fleet 1")
        self.assertEqual(obj.host, host)
        self.assertEqual(obj.doctrine, "see details")
        self.assertEqual(obj.formup_system, EventImport.SPECTRE_FLEET)
        self.assertEqual(obj.description, "")
        published = utc.localize(dt.datetime(2021, 2, 5, 21, 0))
        self.assertEqual(obj.start_time, published)
        self.assertEqual(obj.end_time, published)
        self.assertEqual(obj.fc, EventImport.SPECTRE_FLEET)
        self.assertEqual(obj.visibility, Event.VISIBILITY_EXTERNAL)
        self.assertEqual(obj.user, user)
        self.assertEqual(obj.eve_character, eve_character)
