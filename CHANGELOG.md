# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased] - yyyy-mm-dd

### Added
### Changed
### Fixed

## v2.0.0b - 2021-04-29

Major update for opcalendar which will add a lot of new functions, options and customization options.

### Update from 1.5.1
Update the plugin as you update normal plugins.

- Pull new version `pip install -U aa-opcalendar`
- Run migrations `python manage.py migrate`
- Collect statics `python manage.py collectstatic`

After you have migrated the new models you will need to add a visibility filter. This filter will replace the old hard coded public and member event filters.

- Admin menu -> Event Visibilities Filters -> Add Event Visibility filter. You can determine who is able to see the events labeled with this filter by assigning groups or member states to the filter. Fill in the rest of the settings to this filter based on your needs.

Major changes done in the calendar are listed bellow.

### Added
- Added the ability for members to sign up on events
- Added support for aa-discordbot and command to call for upcoming operations on discord
- Ability to generate ICAL feeds
- Added button to add event on personal calendar from opcalendar
- Added the ability to have an pre-filled descriptions for event categories
- Added ability to display aa-moonmining extractions on calendar
- Added ability to display aa-structuretimers on calendar view
- Added new NPSI feed options
- Ability to filter events by multiple filters at the same time

### Changed
- Event categories hardcoded colors to custom colors
- Event visibility types to customizable
- Minor styling fixes
- Field help text changes

### Removed
- Removed ingame moon event options, replaced with aa-moonmining

### Fixed
- Stripped HTML tags from NPSI imported fleets
- Form default values

## v2.0.0a4

### Fixed
- Ingame events to fall in line with the correct time compared to normal events

### Added
- Support to structure timers plugin

## v2.0.0a3

### Changed
- How ingame event visibility works

### Fixed
- #8
- #9

## v2.0.0a2

### Fixed
- #8
- #9

## v2.0.0a1 - 2021-03-15
This is a major update for opcalendar that will add the option for custom colors, visibility options and ingame event view permissions.

### Added
- Custom colors
- Visibility filters
- Ingame event filters

### To update:
After updating you will need to create new visibility filters (the old public and member filters) and assign states or groups for it. If no states or groups are selected the event with this filter are visible for everyone.

Customize your colors for the visibility filters and for the categories in the admin menu.

Change the permissions for showing ingame events. They can now be restricted to corporation, alliance or all ingame events.

## v1.5.1 - 2021-02-22

### Fixed
- Host not saving on form submit

### Changed
- Discord webhook layouts

### Added
- Logo urls for hosts
- Help descriptions to host add page

## v1.4.0 - 2021-02-01

### Changes

- Adding code-style checks
- Reformatted code to "black" code style so it's better readable
- Fixed quite a number of code issues
- Adding repo url to setup

## v1.3.0 - 2021-01-29

### Changes

- Renamed NPSI import function

### Breaking

- Update your update task to
```
CELERYBEAT_SCHEDULE['import_all_npsi_fleets'] = {
    'task': 'opcalendar.tasks.import_all_npsi_fleets',
    'schedule': crontab(minute=0, hour='*'),
}
```

## v1.2.4 - 2021-01-26

### Fixes

Issue #3 in fleet signals

## v1.1.1 - 2021-01-23

### Fixed
- Issue #1 with CSS

## v1.1.0 - 2021-01-23

### Added
- Setting to send out discord notifications for API imported fleets
