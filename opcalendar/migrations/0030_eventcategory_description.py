# Generated by Django 3.1.2 on 2021-04-13 13:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opcalendar', '0029_auto_20210410_0852'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventcategory',
            name='description',
            field=models.TextField(blank=True, help_text='Prefilled description that will be added on default on the event description.'),
        ),
    ]
