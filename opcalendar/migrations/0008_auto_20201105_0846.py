# Generated by Django 3.1.2 on 2020-11-05 08:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("opcalendar", "0007_eventhost_twitter"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="event",
            unique_together={("title", "start_time")},
        ),
    ]
