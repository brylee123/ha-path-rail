<p align="center">
  <img src="custom_components/path_rail/brand/icon@2x.png" alt="PATH Rail" width="128" height="128">
</p>

# PATH Rail for Home Assistant

[![Release](https://img.shields.io/github/v/release/brylee123/ha-path-rail)](https://github.com/brylee123/ha-path-rail/releases)
[![Validation](https://github.com/brylee123/ha-path-rail/actions/workflows/validate.yml/badge.svg)](https://github.com/brylee123/ha-path-rail/actions/workflows/validate.yml)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2026.10.4%2B-blue)](https://www.home-assistant.io/)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Live PATH train arrivals, service announcements and inferred line status in Home Assistant.
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

- Arrival boards for any of the 13 PATH stations, grouped by the directions the feed supplies.
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

1. Make a backup and download `path_rail-1.3.2.zip` from the
   [latest release](https://github.com/brylee123/ha-path-rail/releases/latest).
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

Each selected station has a service device. For every direction actually supplied by the feed:

| Entity | State and meaning |
| --- | --- |
| Next arrival | First upstream message, such as `3 min` or `Delayed`; full ordered board in the `arrivals` attribute |
| Next arrival countdown | Feed seconds for that same first message, displayed as minutes by default; unknown if delayed, empty, invalid or unsupported text |
| Reported delay | On if any board message explicitly says `Delayed`; off means no explicit delay text, not a guarantee of punctuality |

`ToNY` and `ToNJ` are direction groups, not routes or platforms. One board can mix
multiple destinations. Empty boards produce unknown; absent or stale boards become unavailable.

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

With the captured topology, Journal Square alone creates **15 entities**; all stations
create **75**. Counts depend on boards actually returned. Newly observed directions are
discovered automatically. Removing stations leaves any old registry entries unavailable;
you may remove those entries manually. Selecting the station again reuses its unique IDs.

## Dashboard and automations

Use a standard **Entities** card and select the arrival, countdown, delay and line-status
sensors from the entity picker. Entity IDs depend on your entity registry and language.

For a Markdown card, replace `sensor.replace_with_your_arrival_entity` with your
next-arrival sensor's actual ID. All messages remain in source order:

```yaml
type: markdown
title: PATH departures
content: |-
  {% set board = 'sensor.replace_with_your_arrival_entity' %}
  {% if states(board) in ['unknown', 'unavailable'] %}
  No current arrival board available.
  {% else %}
  {% for train in state_attr(board, 'arrivals') or [] %}
  - **{{ train.target }}** — {{ train.arrival_time_message }}
  {% endfor %}
  {% endif %}
```

To automate a line disruption, use a **State** trigger on that line's service-status
sensor, entering `delayed` or `suspended` as the target state. Add your own notification
action in the automation editor. Do not use a trigger that treats unavailable as Good Service.
The integration defines no custom actions or event types; standard entity automations apply.

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

