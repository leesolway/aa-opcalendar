# Generated by Django 3.1.2 on 2021-01-19 15:45

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("eveonline", "0012_index_additions"),
        ("authentication", "0017_remove_fleetup_permission"),
        ("opcalendar", "0015_eventimport_eve_character"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="general",
            options={
                "default_permissions": (),
                "managed": False,
                "permissions": (
                    ("basic_access", "Can access this app"),
                    ("view_public", "Can see public events"),
                    ("view_member", "Can see member events"),
                    ("view_ingame", "Can see events from ingame calendar"),
                    ("create_event", "Can create and edit events"),
                    ("manage_event", "Can delete and manage signups"),
                    (
                        "add_ingame_calendar_owner",
                        "Can add ingame calendar feeds for their corporation",
                    ),
                ),
            },
        ),
        migrations.CreateModel(
            name="Owner",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="whether this owner is currently included in the sync process",
                    ),
                ),
                (
                    "character",
                    models.ForeignKey(
                        blank=True,
                        default=None,
                        help_text="character used for syncing blueprints",
                        null=True,
                        on_delete=django.db.models.deletion.SET_DEFAULT,
                        related_name="+",
                        to="authentication.characterownership",
                    ),
                ),
                (
                    "corporation",
                    models.OneToOneField(
                        blank=True,
                        default=None,
                        help_text="Corporation owning blueprints, if this is a 'corporate' owner",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to="eveonline.evecorporationinfo",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="IngameEvents",
            fields=[
                (
                    "event_id",
                    models.PositiveBigIntegerField(
                        help_text="The EVE ID of the event",
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("event_start_date", models.DateTimeField()),
                ("event_end_date", models.DateTimeField(blank=True, null=True)),
                ("title", models.CharField(max_length=128)),
                ("text", models.TextField()),
                ("owner_type", models.CharField(max_length=128)),
                ("owner_name", models.CharField(max_length=128)),
                ("importance", models.CharField(max_length=128)),
                ("duration", models.CharField(max_length=128)),
                (
                    "owner",
                    models.ForeignKey(
                        help_text="Event holder",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="opcalendar.owner",
                    ),
                ),
            ],
        ),
    ]
