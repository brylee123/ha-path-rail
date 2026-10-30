"""PATH Rail custom integration."""

import asyncio

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import PathApi
from .coordinator import PathConfigEntry, PathCoordinator
from .registry import async_finish_registry, async_prepare_registry
from .service_api import ServiceApi
from .service_coordinator import ServiceCoordinator

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: PathConfigEntry) -> bool:
    """Validate the feed before loading platforms; let HA retry setup failures."""
    coordinator = PathCoordinator(hass, entry, PathApi(async_get_clientsession(hass)))
    await coordinator.async_config_entry_first_refresh()
    service_api = ServiceApi(async_get_clientsession(hass))
    coordinator.services = {
        "alerts": ServiceCoordinator(hass, entry, "alerts", service_api.async_fetch_alerts, 60),
        "planned": ServiceCoordinator(
            hass, entry, "planned notices", service_api.async_fetch_planned, 900
        ),
        "site": ServiceCoordinator(hass, entry, "timetable", service_api.async_fetch_site, 21600),
    }
    # An optional feed outage must not block working arrivals. Unavailable source
    # entities still subscribe and recover through their independent coordinator.
    await asyncio.gather(*(source.async_refresh() for source in coordinator.services.values()))
    entry.runtime_data = coordinator
    rename_candidates = async_prepare_registry(hass, entry)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    async_finish_registry(hass, rename_candidates)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    return True


async def _async_options_updated(hass: HomeAssistant, entry: PathConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: PathConfigEntry) -> bool:
    """Unload platforms and their polling listeners."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_migrate_entry(hass: HomeAssistant, entry: PathConfigEntry) -> bool:
    """Remove the former polling option while keeping entry and entity identity."""
    if entry.version > 2:
        return False
    if entry.version == 1:
        data = {key: value for key, value in entry.data.items() if key != "poll_interval"}
        options = {key: value for key, value in entry.options.items() if key != "poll_interval"}
        hass.config_entries.async_update_entry(entry, data=data, options=options, version=2)
    return True
