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
DIRECTIONS = {"ToNY": "toward New York", "ToNJ": "toward New Jersey"}
