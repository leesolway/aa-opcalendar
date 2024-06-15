# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

<!--
GitHub MD Syntax:
https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax

Highlighting:
https://docs.github.com/assets/cb-41128/mw-1440/images/help/writing/alerts-rendered.webp

> [!NOTE]
> Highlights information that users should take into account, even when skimming.

> [!IMPORTANT]
> Crucial information necessary for users to succeed.

> [!WARNING]
> Critical content demanding immediate user attention due to potential risks.
-->

## \[In Development\] - Unreleased

<!--
Section Order:

### Added
### Fixed
### Changed
### Deprecated
### Removed
### Security
-->

## [3.0.0b3] - 2024-05-29

> **IMPORTANT**
>
> **This is a beta release do not use in production**

> **IMPORTANT**
>
> **This version needs at least Alliance Auth v4.0.0!**
>
> Please make sure to update your Alliance Auth instance **before**
> you install this version, otherwise, an update to Alliance Auth will
> be pulled in unsupervised.

If you are using the ical feed for publishing your ops as public you will need to add APPS_WITH_PUBLIC_VIEWS setting to your settings file. See readme for guide.

### Added
- Show a counter for events that the user has not signed up for. Only shows standard events (excluded imported NPSI events)
- Added new setting OPCALENDAR_SHOW_EVENT_COUNTER
- Ability to sign up with different states and add comments to signups, Closes #31
- Compatibility to Alliance Auth v4
    - Bootstrap 5
- Translation tags
- Added OPCALENDAR_NOTIFY_REPEAT_EVENTS setting allowing to disable discord notifications for repeating events. Closes #33
- Added filter to NPSI fleets. Closes #29
- Added setting to use localtimes in calendar view
- Added FC name to calendar feed, closes #38
### Changed
- Calendar view template
- Moved information about local time and moon mining timers to the legend section
- Changed how the ical feed is set up using the APPS_WITH_PUBLIC_VIEWS, Closes #36
- Merged light and dark stylesheets in one file

### Fixed
- Fixed local times on event details, Closes !7

### Removed
- Dropped support for alliance Auth 3

## [2.4.0] - 2023-03-16

### Added
- Added slash command for !ops

## [2.3.1] - 2023-03-22

### Fixed

- Error in fetching fleets (#30) thx [Erik Kalkoken](https://gitlab.com/ErikKalkoken)

## [2.3.0] - 2022-05-22

Added new app settings to customize the aa-moonmining fractures displayed in the opcalendar.

## Added

- Added the ability to label aa-moonmining events on calendar with rarity labels
- Added the ability to change displayed aa-moonmining events timer to auto fracture timer

## [2.2.3] - 2022-03-05

### Fixed

- AA3 compatibility fixes

## [v2.2.2] - 2022-02-06

### Changed

- Changed bot command to return 10 fleets instead of 20 due to max character limit issues

## [v2.2.1] - 2022-02-06

### Fixed

- Fixes #26, fix webhooks not sending for new created events
- Fixes #25, removed unused fields from edit event view

## [v2.2.0] - 2022-01-15

### Added

- Added ability to make repeating events for weekly intervals

## [v2.1.0] - 2022-01-15

### Added

- Closes #23, added ability to make diplicates when creating an event

## [v2.0.3] - 2022-01-10

### Fixed

- #24, fixed canceled moonmining extractions showing up on calendar

## [v2.0.2] - 2021-12-22

### Added

- Different style files for light and dark themes

### Fixed

- #20 for visibility reseting to default
- #22 light theme issues

## v2.0.1 - 2021-05-14

### Fixed

- Errors for NPSI event import when visibility group has no webhook selected
- Errors in NPSI import task for missing events

## v2.0.0b1 - 2021-05-03

### Added

- Filter for moonmining
- Filter for structuretimers

### Changed

- Displaying chunk arrival time of moonmining instead of autofracture time

## v2.0.0b - 2021-04-29

Major update for opcalendar which will add a lot of new functions, options and customization options.

### Update from 1.5.1

Update the plugin as you update normal plugins.

- Pull new version `pip install -U aa-opcalendar`
- Run migrations `python manage.py migrate`
- Collect statics `python manage.py collectstatic`

After you have migrated the new models you will need to add a visibility filter. This filter will replace the old hard coded public and member event filters.

- Admin menu -> Event Visibilities Filters -> Add Event Visibility filter. You can determine who is able to see the events labeled with this filter by assigning groups or member states to the filter. Fill in the rest of the settings to this filter based on your needs.

- Update NPSI event import settings from admin menu

- Update ingame events settings from admin menu

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

### To update

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

## [Unreleased] - yyyy-mm-dd

### Added

### Changed

### Fixed
