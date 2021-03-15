# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## v2.0.0a1 - 2021-03-15
This is a major update for opcalendar that will add the option for custom colors, visibility options and ingame event view permissions.

## Added
- Custom colors
- Visibility filters
- Ingame event filters

## To update:
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
