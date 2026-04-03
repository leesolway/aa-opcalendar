from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("opcalendar", "0030_add_use_24h_to_usersettings"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="is_cancelled",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="event",
            name="cancellation_reason",
            field=models.TextField(blank=True, default=""),
        ),
    ]
