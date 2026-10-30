# Changelog

## 1.5.0 (development preview)

- Consolidate line-status sensors under PATH Line Status and diagnostics under PATH Service.
- Shorten line, destination and combined-direction names and migrate automatically assigned entity IDs while retaining custom IDs.
- Add independent source-status and last-successful-fetch diagnostics that remain readable through outages.
- Expose oldest and newest arrival prediction update times separately from download time.
- Keep combined NY Bound / NJ Bound boards available but disabled by default.

## 1.4.0

- Add destination-specific arrival, countdown and reported-delay entities with dynamic support for unusual service destinations.
- Expose validated per-prediction colors, including multi-color services.
- Support the separately installable PATH Rail Arrivals Card with single-direction and bidirectional layouts, a visual configuration form and a station/service alert ticker.
- Add automatic, light and dark appearance options to the arrival-board card.
- Preserve existing direction entity identities; new installations use destination entities by default.
- Clarify that prediction freshness and the fixed polling interval are separate settings.

## 1.3.2

- Add US regional metadata for HACS catalog submission.
- Publish an updated installation package with validated Home Assistant and HACS metadata.

## 1.3.1

- Publish the integration in its own public GitHub repository with real owner, documentation and issue-tracker metadata.
- Replace generic branding with the supplied PATH image and standard/high-resolution local icons.
- Add complete setup, HACS custom repository, entity, troubleshooting and upgrade documentation.
- Add public CI, issue templates and release packaging. Entity behavior and the pinned PyPI client are unchanged.

## 1.3.0

- Install `panynj-ridepath-client==0.2.0` from PyPI and remove bundled client code.

## 1.2.0

- Add service/accessibility announcements, planned content and five inferred line-status sensors.

## 1.1.0

- Extract an independent async client; fixed polling, translated entities and version-2 configuration migration.

## 1.0.0

- Initial station/direction arrival boards, countdowns, reported delays, setup/options and diagnostics.
