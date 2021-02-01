# Generated by Django 3.1.2 on 2020-11-05 08:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("opcalendar", "0008_auto_20201105_0846"),
    ]

    operations = [
        migrations.AlterField(
            model_name="event",
            name="doctrine",
            field=models.CharField(blank=True, default="", max_length=254),
        ),
        migrations.AlterField(
            model_name="event",
            name="formup_system",
            field=models.CharField(blank=True, default="", max_length=254),
        ),
        migrations.AlterField(
            model_name="event",
            name="host",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                to="opcalendar.eventhost",
            ),
        ),
    ]
