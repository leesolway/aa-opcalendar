# Operation Calendar

An operation calendar app for Alliance Auth to display fleet operations and other events.

![release](https://img.shields.io/pypi/v/aa-opcalendar??label=release) ![python](https://img.shields.io/pypi/pyversions/aa-opcalendar?) ![license](https://img.shields.io/badge/license-MIT-green)

## Includes:
 * Calendar type view of events and fleets
 * Custom event categories
 * Custom hosts
 * Public and member restricted events
 * Detailed view for events
 * Webhook for discord notifications
 * Importing NPSI fleets from public sources
 * Importing fleets from corporation ingame calendar

![screenshot](https://i.imgur.com/bLepJGH.jpg)
 
## Installation
 1. Install the Repo `pip install aa-opcalendar`
 2. Add `'opcalendar',` to your `INSTALLED_APPS` in your projects `local.py`
 3. run migrations and restart auth
 4. setup your perms as documented below

## Permissions

Perm | Auth Site | Example Target Group
 --- | --- | ---
opcalendar basic_access | Can view the calendar page. | Guest and Members
opcalendar view_public | Can view events with public visibility. | Guest and Members
opcalendar view_member | Can view events with member only visibility. | Members
opcalendar view_ingame | Can view events that have been imported from the ingame calendars | Members
add_ingame_calendar_owner | Can add feeds for ingame calendar events | CEOs and Directors
opcalendar create_event | Can create events. | Fleet Commanders

## Settings

Name | Description | Default
 --- | --- | ---
OPCALENDAR_NOTIFY_IMPORTS | Wheter to automatically send out discord notifications for fleets imported and deleted via API sources such as ingame calendar or the pre determined sources | True

## Usage
In order to use the calendar and create event you will need to create event hosts and event categories.

- Go to the admin site 
- **Add a Host**. The first host is most likely your own alliance/corporation. Fill in at least the community name ie. your alliance name. This name will be displayed on the calendar view on the event block. You may fill in additional information which will be displayed on the detailed view for the event.
- **Add a category**. Next you will need to add at least one category for your events. Categories can be whatever you want to have such as STRATOP, mining, roam etc. The ticker for the event will be displayed both on the calendar view event block and on the detailed view for the event.
- **Webhook for discord notifications (optional)**. If you want to receive notifications about your events (created/modified/deleted) on your discord you can add a webhook for the channel in discord you want to receive the notifications to. Add a webhook and connect it to the fleet signals.
- **Add new event**. To add new events simply go to the operation calendar and click on the add event button. Fill in the information for your event.


### Importing NPSI fleets
Opcalendar has  the ability to import predetermined NPSI fleets directly into your calendar. These operations will be labeled as `imported` operations.

Opcalendar is currently supporting imports for the following NPSI fleets:

- Spectre fleet
- Eve University (classes only)

To start importing fleets:

- **Go to admin panel and select Event Imports**
- **Create a host** for each import and fill in the needed details for them.
- **Add a new import** by pressing on the add event import button
- **Select the source** where you want to fetch the fleets.
- **Determine operation type** for each fetched fleet.

**WARNING: Running the import function will delete all fleets labaled with the import label to get rid of possibly deleted operations.**

To schedule the import runs either add the following line in your local.py file or set up a perioduc task for the `opcalendar.tasks.import_fleets` task on your admin menu to fetch fleets every hour.

```
CELERYBEAT_SCHEDULE['import_fleets'] = {
    'task': 'opcalendar.tasks.import_fleets',
    'schedule': crontab(minute=0, hour='*'),
}

```

### Importing fleets from ingame calendar
You can import events that have been created in the ingame calendar. As the fields on the ingame calendar are limited the events will not be as detailed as when created directly from the calendar.

1. Give the add_ingame_calendar_owner role for the wanter groups
2. Navigate to the opcalendar page and press the `Add Ingame Calendar Feed` button
3. Log in with the character that holds the calendar
4. Add the following line into your local.py setting file or set up a periodic task for the `opcalendar.tasks.update_all_ingame_events` to pull fleets from ingame every 5 minutes.

```
CELERYBEAT_SCHEDULE['update_all_ingame_events'] = {
    'task': 'opcalendar.tasks.update_all_ingame_events',
    'schedule': crontab(minute='*/5'),
}
```

## Contributing
Make sure you have signed the [License Agreement](https://developers.eveonline.com/resource/license-agreement) by logging in at https://developers.eveonline.com before submitting any pull requests. All bug fixes or features must not include extra superfluous formatting changes.
