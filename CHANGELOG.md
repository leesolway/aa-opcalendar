# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

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
