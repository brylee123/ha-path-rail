"""Constants for PATH Rail."""

DOMAIN = "path_rail"
NAME = "PATH Rail"
FEED_URL = "https://www.panynj.gov/bin/portauthority/ridepath.json"
CONF_STATIONS = "stations"
CONF_STALE_AFTER = "stale_after"
POLL_INTERVAL = 30
DEFAULT_STALE_AFTER = 300
MAX_RESPONSE_BYTES = 1024 * 1024
STATIONS = {
    "NWK": "Newark",
    "HAR": "Harrison",
    "JSQ": "Journal Square",
    "GRV": "Grove Street",
    "NEW": "Newport",
    "EXP": "Exchange Place",
    "HOB": "Hoboken",
    "WTC": "World Trade Center",
    "CHR": "Christopher Street",
    "09S": "9th Street",
    "14S": "14th Street",
    "23S": "23rd Street",
    "33S": "33rd Street",
}
DIRECTIONS = {"ToNY": "NY Bound", "ToNJ": "NJ Bound"}

# Normal terminal names and board directions, not an allowlist for live predictions.
DESTINATIONS = {code: STATIONS[code] for code in ("33S", "WTC", "NWK", "HOB", "JSQ")}
STATION_DESTINATIONS = {
    "NWK": {"WTC": ("ToNY",)},
    "HAR": {"NWK": ("ToNJ",), "WTC": ("ToNY",)},
    "JSQ": {"NWK": ("ToNJ",), "WTC": ("ToNY",), "33S": ("ToNY",)},
    "GRV": {"NWK": ("ToNJ",), "JSQ": ("ToNJ",), "WTC": ("ToNY",), "33S": ("ToNY",)},
    "NEW": {"JSQ": ("ToNJ",), "HOB": ("ToNJ",), "WTC": ("ToNY",), "33S": ("ToNY",)},
    "EXP": {"NWK": ("ToNJ",), "HOB": ("ToNJ",), "WTC": ("ToNY",)},
    "HOB": {"WTC": ("ToNY",), "33S": ("ToNY",), "JSQ": ("ToNY", "ToNJ")},
    "WTC": {"NWK": ("ToNJ",), "HOB": ("ToNJ",)},
    **{
        code: {"JSQ": ("ToNJ",), "HOB": ("ToNJ",), "33S": ("ToNY",)}
        for code in ("CHR", "09S", "14S", "23S")
    },
    "33S": {"JSQ": ("ToNJ",), "HOB": ("ToNJ",)},
}

LINE_STATIONS = {
    "red": ("NWK", "HAR", "JSQ", "GRV", "EXP", "WTC"),
    "yellow": ("JSQ", "GRV", "NEW", "CHR", "09S", "14S", "23S", "33S"),
    "green": ("HOB", "NEW", "EXP", "WTC"),
    "blue": ("HOB", "CHR", "09S", "14S", "23S", "33S"),
    "night-yellow": ("JSQ", "GRV", "NEW", "HOB", "CHR", "09S", "14S", "23S", "33S"),
}

# Short presentation labels; upstream identifiers and model names remain unchanged.
STATION_LABELS = {"33S": "33", "09S": "9", "14S": "14", "23S": "23"}
LINE_LABELS = {
    "red": "NWK-WTC",
    "yellow": "JSQ-33",
    "green": "HOB-WTC",
    "blue": "HOB-33",
    "night-yellow": "JSQ-33 via HOB",
}
