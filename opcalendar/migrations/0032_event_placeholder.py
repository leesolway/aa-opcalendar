from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("opcalendar", "0031_event_cancellation"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="is_placeholder",
            field=models.BooleanField(default=False),
        ),
    ]
