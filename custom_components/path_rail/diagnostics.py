"""Downloadable public-feed diagnostics; no credentials or location data."""

from homeassistant.core import HomeAssistant

from .coordinator import PathConfigEntry


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: PathConfigEntry) -> dict:
    coordinator = entry.runtime_data
    return {
        "settings": {**entry.data, **entry.options},
        "last_update_success": coordinator.last_update_success,
        "consecutive_failures": coordinator.failures,
        "last_successful_fetch": coordinator.data.fetched_at.isoformat(),
        "announcement_sources": {
            name: {
                "last_update_success": source.last_update_success,
                "consecutive_failures": source.failures,
                "fetched_at": source.data.fetched_at.isoformat() if source.data else None,
            }
            for name, source in coordinator.services.items()
        },
        "boards": [
            {
                "station": board.station,
                "direction": board.direction,
                "arrivals": [arrival.as_dict() for arrival in board.arrivals],
            }
            for key, board in coordinator.data.boards.items()
            if key[0] in coordinator.stations
        ],
    }
