"""One polling coordinator for all configured stations."""

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CannotConnect, PathApi, RateLimited
from .const import (
    CONF_STALE_AFTER,
    CONF_STATIONS,
    DEFAULT_STALE_AFTER,
    DOMAIN,
    POLL_INTERVAL,
)
from .models import Feed, InvalidFeed

_LOGGER = logging.getLogger(__name__)

type PathConfigEntry = ConfigEntry[PathCoordinator]


class PathCoordinator(DataUpdateCoordinator[Feed]):
    """Share one request, including failures and recovery, between entities."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: PathApi) -> None:
        settings = {**entry.data, **entry.options}
        self.api = api
        self.stations = tuple(settings[CONF_STATIONS])
        self.poll_interval = POLL_INTERVAL
        self.stale_after = settings.get(CONF_STALE_AFTER, DEFAULT_STALE_AFTER)
        self.failures = 0
        self.services = {}
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=self.poll_interval),
        )

    async def _async_update_data(self) -> Feed:
        try:
            data = await self.api.async_fetch()
        except (CannotConnect, InvalidFeed) as err:
            self.failures = min(self.failures + 1, 6)
            delay = min(self.poll_interval * 2**self.failures, 900)
            if isinstance(err, RateLimited):
                delay = max(delay, err.seconds)
            self.update_interval = timedelta(seconds=delay)
            raise UpdateFailed(translation_domain=DOMAIN, translation_key="update_failed") from err
        self.failures = 0
        self.update_interval = timedelta(seconds=self.poll_interval)
        return data
