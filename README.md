<p align="center">
  <img src="custom_components/path_rail/brand/icon@2x.png" alt="PATH Rail" width="128" height="128">
</p>

# PATH Rail for Home Assistant

**Development preview: 1.4.0b0.** This branch adds destination boards and the optional dashboard card. The current stable release does not yet contain these features.

[![Release](https://img.shields.io/github/v/release/brylee123/ha-path-rail)](https://github.com/brylee123/ha-path-rail/releases)
[![Validation](https://github.com/brylee123/ha-path-rail/actions/workflows/validate.yml/badge.svg)](https://github.com/brylee123/ha-path-rail/actions/workflows/validate.yml)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2026.10.4%2B-blue)](https://www.home-assistant.io/)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Destination-specific PATH train arrivals, service announcements and inferred line status in Home Assistant.
Built for Home Assistant OS, including Raspberry Pi 4. No account, API key, MQTT broker
or separate server is needed. This is an **unofficial community integration**, unaffiliated
with the Port Authority of New York and New Jersey (PANYNJ).

[![Add this repository to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=brylee123&repository=ha-path-rail&category=integration)
[![Add PATH Rail to Home Assistant](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=path_rail)

Install the integration first, then use **Add PATH Rail**. This repository can be added
as a custom integration repository; it is not listed in the HACS default catalog.

## Contents

[Features](#features) · [Requirements](#requirements) · [Installation](#installation) ·
[Configuration](#configuration) · [Entities](#entities) · [Dashboard and automations](#dashboard-and-automations) ·
[Updates and removal](#updates-and-removal) · [Troubleshooting](#troubleshooting) ·
[Limitations](#limitations) · [Development](#development) · [Support and licensing](#support-and-licensing)

## Features

- Arrival boards for any of the 13 PATH stations, grouped by the actual destination reported by the feed.
- Next-arrival text, numeric countdown when supported, and an explicit reported-delay sensor.
- Service alerts, elevator/escalator notices and published planned service changes.
- A service-status sensor for each of five PATH lines, with **Delayed**, **Suspended**,
  **Good Service** and **Not Scheduled** states when the inputs support a conclusion.
- UI setup and options, stable entity identities, automatic board discovery, diagnostics,
  independent source availability, asynchronous requests and upstream rate-limit handling.
- Local PATH icons for the Home Assistant integration card and logo fallback.

**Line statuses are inferred, not authoritative API values.** Read the attached messages;
Good Service is not a guarantee of punctual service. Ambiguous data produces unknown,
and failed required sources produce unavailable.

## Requirements

| Requirement | Details |
| --- | --- |
| Home Assistant | Core **2026.10.4 or newer** |
| Installation type | Home Assistant OS, Container or Core; 64-bit HA OS recommended on Raspberry Pi 4 |
| Network | HTTPS to `www.panynj.gov`; `pypi.org` and `files.pythonhosted.org` during dependency installation/updates |
| Clock | Correct system time; source timestamps determine arrival freshness |
| Credentials | None |
| Python dependency | `panynj-ridepath-client==0.2.0`, installed automatically by Home Assistant |

You do not install Python, run pip, or add host packages on Home Assistant OS.

## Installation

### HACS custom repository

1. Open **HACS → ⋮ → Custom repositories**.
2. Add `https://github.com/brylee123/ha-path-rail` with type **Integration**.
3. Find **PATH Rail** and download it.
4. Restart Home Assistant when prompted.
5. Open **Settings → Devices & services → Add integration → PATH Rail**.
6. Select your stations and finish setup.

The HACS badge above opens the custom-repository form in your own Home Assistant.
If your installed repository manager uses different menu labels, add the same GitHub URL
as an integration. Manual installation below remains available.

### Manual installation on Home Assistant OS

1. Make a backup and download `path_rail-1.4.0b0.zip` from the development-preview download supplied with this branch. Stable releases remain on the
   [releases page](https://github.com/brylee123/ha-path-rail/releases).
2. Extract the ZIP on your computer. With the **Samba share** or **Studio Code Server**
   app, copy its `custom_components/path_rail` directory into `/config/custom_components/`.
3. Confirm the final path is `/config/custom_components/path_rail/manifest.json`.
   Do not add an extra parent directory or copy the Python client library there.
4. Restart Home Assistant, then add **PATH Rail** in **Settings → Devices & services**.

For a GitHub source archive, the component is inside the archive's repository folder.
Only copy the `path_rail` directory. No full OS reboot is needed.

## Configuration

Setup is entirely through the UI; there is no YAML configuration. One integration entry
serves the network. Open its **Configure** button to change options; it reloads automatically.

| Option | Default | Values |
| --- | --- | --- |
| Stations | Journal Square | One or more of the stations below |
| Maximum source age | 300 seconds | 120–1800 seconds |

Polling intervals are chosen by the integration:

| Resource | Normal interval |
| --- | --- |
| Arrivals | 30 seconds, one shared request for all stations |
| Service/accessibility alerts | 60 seconds |
| Planned changes | 15 minutes |
| Website timetable/configuration | 6 hours, two GET requests |

Arrival errors back off up to 15 minutes; a success restores the normal interval.
HTTP 429/503 Retry-After deadlines are respected independently for each resource.

### Supported stations

| Code | Station | Code | Station |
| --- | --- | --- | --- |
| NWK | Newark | HAR | Harrison |
| JSQ | Journal Square | GRV | Grove Street |
| NEW | Newport | EXP | Exchange Place |
| HOB | Hoboken | WTC | World Trade Center |
| CHR | Christopher Street | 09S | 9th Street |
| 14S | 14th Street | 23S | 23rd Street |
| 33S | 33rd Street | | |

## Entities

Each selected station has a service device. Arrival entities are grouped by **destination**,
using upstream `target` codes. The normal terminal names are 33rd Street (`33S`),
World Trade Center (`WTC`), Newark (`NWK`), Hoboken (`HOB`) and Journal Square (`JSQ`).
Normal station connections determine the usual boards, not a whitelist: a reported
unusual destination such as Grove Street is discovered automatically and is not discarded.
The feed's destination is authoritative even if a rare service change differs from the normal network.

| Entity | State and meaning |
| --- | --- |
| World Trade Center next arrival (example) | First matching upstream message, such as `3 min` or `Delayed`; all matching trains remain in the `arrivals` attribute |
| World Trade Center next arrival countdown | Feed seconds for that same matching message; unknown for delayed/unsupported text or an empty destination board |
| World Trade Center reported delay | On if any matching message explicitly says `Delayed`; off is not a guarantee of punctual service |

The same three entities are created for each normal destination at the selected station.
A healthy source with no matching prediction produces unknown, not Not Scheduled.
Missing source boards or stale matching predictions produce unavailable. Freshness is
checked per destination, so an old WTC prediction does not hide a fresh 33rd Street train.
Known destinations use stable canonical names; unexpected destinations use their station
name or reported headsign. Existing unexpected destinations stay registered if they
temporarily disappear; after a reload they are rediscovered when reported again.

Original **Toward New York/New Jersey** entities retain their unique IDs and existing
registry settings. They are disabled by default for new entity registry entries. Existing
dashboards can keep using them; disable them manually when migrating to destination cards.
Arrival, countdown and delay entity IDs remain separate for direction and destination boards.

The next-arrival sensor exposes `destination_code`, `destination`, `station_code`,
`station_name`, `source_directions`, `arrivals`, `arrival_count`, `color`, `colors`
and `fetched_at`. Each arrival keeps the original target, text, raw validated seconds,
headsign, source timestamp and `line_color`, plus CSS-ready `colors` (for example
`["#D93A30"]`). `color` is populated only when there is a single color; multi-color
trains retain every color instead of inventing one. Different trains to WTC can have
different colors. Colors come from the feed, not a fixed destination-to-color mapping.

The integration also creates these entities regardless of the selected arrival stations:

| Entity | State and attributes |
| --- | --- |
| Feed status (diagnostic) | `ok`, `stale`, `missing_station`, `empty`, `error`; source health and failure details |
| Alerts | Count of latest incident updates, including resolved records; `announcements` and `active_count` |
| Elevator and escalator alerts | Count of categorized accessibility notices, including resolved records; source/station tags |
| Planned service changes | Count of published notices; titles, plain-text descriptions and HTTP(S) links |
| Five line service-status sensors | Inferred enum status, attached notices, schedule context and source fetch times |

The five lines are **Newark–WTC**, **Journal Square–33rd Street**, **Hoboken–WTC**,
**Hoboken–33rd Street**, and **Journal Square–33rd Street via Hoboken** (overnight service).

| Display label | Native state for automations |
| --- | --- |
| Delayed | `delayed` |
| Suspended | `suspended` |
| Good Service | `good_service` |
| Not Scheduled | `not_scheduled` |

Normal destination boards create 18 enabled entities with Journal Square selected,
or 117 when all stations are selected (including the nine service/diagnostic entities).
Additional unexpected destinations create additional entities when reported. Legacy
direction entities are separate and may remain enabled on upgrades.

## Dashboard and automations

Standard Entities/Tile cards can display the destination sensors. Home Assistant has
no generic sensor setting that automatically paints those cards using a `color` attribute.
For colored train rows and the alert ticker, install the optional bundled card:

1. Copy `custom_components/path_rail/www/path-rail-arrivals-card.js` to
   `/config/www/path-rail-arrivals-card.js`. Create `/config/www` if needed. The preview
   download also supplies the JavaScript as a separate file for this step.
2. In **Settings → Dashboards → Resources** (enable Advanced mode in your profile if
   needed), add `/local/path-rail-arrivals-card.js?v=1.4.0b0` as a **JavaScript module**.
   If the `www` folder is newly created, restart Home Assistant; then refresh the browser.
3. Add the **PATH arrival board** community card in the dashboard editor. Choose
   **Single direction** or **Bidirectional** and select destination next-arrival sensors.
   Do not select countdown sensors. The card has a visual configuration form.
4. For bidirectional mode, select the left and right destination groups and optional
   headings. These are display groups chosen by you; the feed does not supply physical
   platform numbers. Choose a larger width if long destination names wrap.

Single direction (replace the example ID using your entity picker):

```yaml
type: custom:path-rail-arrivals-card
mode: single
title: PATH — World Trade Center
entities:
  - sensor.replace_with_your_wtc_next_arrival
max_rows: 2
show_alerts: true
```

Bidirectional:

```yaml
type: custom:path-rail-arrivals-card
mode: bidirectional
title: PATH Journal Square
left_title: World Trade Center / 33rd Street
left_entities:
  - sensor.replace_with_your_wtc_next_arrival
  - sensor.replace_with_your_33rd_street_next_arrival
right_title: Newark
right_entities:
  - sensor.replace_with_your_newark_next_arrival
max_rows: 2
show_alerts: true
```

With one destination selected, rows show successive predictions in source order. With
several destinations on a side, the card shows each destination's first prediction before
its later predictions, following your selection order. It does not invent train IDs or
sort delayed trains using unreliable raw seconds. Tap a row to open entity details.
Unavailable entities never render retained old train predictions. Unknown/missing colors
use a neutral dot; a multi-color prediction uses a split-color dot.

The ticker automatically finds PATH service and accessibility alert sensors. Active
station-tagged notices, notices mentioning a line that serves the station, and unscoped
PATH notices are included. `related_stations` is derived from station tags and normal
routes mentioned in the message, not an authoritative impact list. Unscoped notices
are included conservatively; they are not proof the source declared a system-wide incident.
Closed updates are excluded and duplicate incidents appear once. Planned notices are
not treated as active disruptions. Failed/missing alert sources show an explicit message,
never an all-clear. The eight-hour source window can omit older unresolved incidents.

Station is detected from the selected arrival sensors. Select one station per card or
set the **Station for alerts** option explicitly. **Alert sensors** is optional; leave it
empty for automatic discovery. Scrolling pauses on hover or keyboard focus, and reduced
motion settings show wrapped static text. The footer clock is browser-local wall time;
arrival countdowns remain 30-second feed snapshots. Update the copied JavaScript and
resource version after updating the card; HACS does not update your `/config/www` copy.

For automations, use the destination delay binary sensor, or a State trigger on a line
status with `delayed` or `suspended`. The integration defines no custom actions/events.

## Updates and removal

Update through HACS and restart Home Assistant. For manual updates, **replace the entire**
`/config/custom_components/path_rail` folder. This removes obsolete files, including the
`_vendor` directory from versions before 1.3.0. Home Assistant installs the pinned client
dependency automatically. Existing config-entry identity and entity unique IDs are retained.

Version-1 configuration entries migrate automatically: station choices and source-age
settings remain, while the former adjustable polling setting is removed. Restore a backup
before downgrading to 1.0.0 after that migration.

To uninstall, remove the PATH Rail entry in **Settings → Devices & services**, remove the
repository in HACS (or delete its component folder for a manual installation), and restart.
Remove unused dashboard cards and automations separately.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| PATH Rail is missing from Add integration | Verify the exact manifest path, restart HA and refresh the frontend |
| Dependency installation failed | Check internet access, DNS, system clock and PyPI access; never run pip inside HA OS |
| Arrivals are unavailable | Check feed-status diagnostics, source timestamps, configured source age and upstream availability |
| Only alerts or line status are unavailable | Their sources fail independently; working arrival boards can remain available |
| Countdown is unknown for a delayed train | Intentional: raw seconds paired with `Delayed` are not a reliable ETA |
| A line status is unknown | Alert wording or timetable inputs cannot support a safe inference |
| Old logo remains | Replace the complete component folder, restart HA and hard-refresh the browser; brand images can be cached |

Open **Settings → System → Logs** for `path_rail` messages. From the integration menu,
download diagnostics and enable debug logging when reporting a problem. Review diagnostic
files before posting: they include your selected stations and public source information.
Do not post Home Assistant tokens, unrelated logs or private configuration.

## Limitations

- Public website endpoints have no established uptime or schema guarantee. Failed or
  malformed responses are not treated as an all-clear, and fixtures are never an offline fallback.
- Countdown values are feed snapshots, not a per-second clock. No reliable platform,
  train ID, delay duration, scheduled arrival time or cancellation flag is supplied.
- Next arrival means first upstream message. Raw seconds can disagree with delay text;
  invalid, missing, old or implausibly future timestamps make affected boards unavailable.
- Good Service means scheduled by the website timetable with no identified current
  disruption in fetched alerts. The eight-hour alert window may omit older unresolved incidents.
- Closed incident updates supersede older revisions. Ambiguous active alerts produce
  unknown. A partial suspension may affect the line sensor; read its attached message.
- Planned content can describe future work and does not itself set live line status.
- Schedule inference uses America/New_York and website day/night boundaries. Holiday
  data approximates the site's calendar for **2026–2032**; outside coverage, schedule-dependent
  status is unknown. Special schedules may differ from the normal timetable.
- Previously tested with real HA helpers on Linux, not yet installed on a physical Raspberry Pi.
  No long-running soak test or official quality-scale certification is claimed.

Arrival board lists and fetch-time attributes are excluded from recorder history to reduce
storage churn; they remain available in live state/templates. Countdown sensors have no
long-term statistics state class. The integration sends no analytics or telemetry of its own;
requests go to the listed public feeds and dependency hosts.

## Development

The API client is maintained separately at
[panynj-ridepath-client](https://github.com/brylee123/panynj-ridepath-client) and
[published on PyPI](https://pypi.org/project/panynj-ridepath-client/).
No client implementation is vendored in this repository. The HA layer owns freshness,
incident classification, schedule/status inference and entity presentation.

On Linux with Python 3.14.2 or newer:

```sh
python -m venv .venv
. .venv/bin/activate
pip install ruff
ruff check .
ruff format --check .
```

CI checks code style and runs the required hassfest and HACS validation actions.
The integration test suite is not included in this repository. See [CONTRIBUTING.md](CONTRIBUTING.md)
and [CHANGELOG.md](CHANGELOG.md).

## Support and licensing

[Report a bug or request a feature](https://github.com/brylee123/ha-path-rail/issues).
Include your HA version, integration version, expected behavior and relevant diagnostics.
For real rail service information, consult [official PATH information](https://www.panynj.gov/path/en/index.html).

Code is [MIT licensed](LICENSE). The PATH name and supplied PATH logo identify the
service and remain the property of their respective rights holders; they are not covered
by the code's MIT license. The logo was supplied for this project and is included unchanged
at 512 pixels, with a 256-pixel icon copy. There is no affiliation or endorsement.
Generated holiday data has separate [CC BY 3.0 attribution](custom_components/path_rail/SITE_CALENDAR_LICENSE.md).

See [third-party notices](THIRD_PARTY_NOTICES.md) for feed and artwork attribution.

