# Contributing

Open an issue before changing feed interpretation or entity identities. Include a minimal,
redacted source example and distinguish observed upstream fields from inferred behavior.

Use Python 3.14.2+ on Linux. Install Ruff in a virtual environment; run `ruff check .` and `ruff format --check .`.
CI also checks hassfest and HACS compatibility. Verify behavior in a development
Home Assistant instance before publishing changes.

Keep HTTP/protocol changes in the separate panynj-ridepath-client repository. This
integration pins a published version and must not copy the client into its component.
Keep translations/en.json synchronized with strings.json and retain stable unique IDs.

For releases, update manifest.json and CHANGELOG.md, verify CI, then publish a GitHub
release named vX.Y.Z matching the manifest. CI reruns validation and attaches a manual
installation ZIP. Keep the component domain path_rail unchanged. No PyPI upload belongs
in the integration release workflow.

The PATH artwork and generated calendar data have separate rights/attribution; see README
and custom_components/path_rail/SITE_CALENDAR_LICENSE.md. Review diagnostics and logs for private details before posting.
