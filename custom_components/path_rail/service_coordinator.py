"""Independently poll announcements so failures do not disable arrivals."""

import logging
from collections.abc import Awaitable, Callable
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CannotConnect, RateLimited
from .coordinator import PathConfigEntry
from .models import InvalidFeed

_LOGGER = logging.getLogger(__name__)


class ServiceCoordinator(DataUpdateCoordinator[Any]):
    def __init__(
        self,
        hass: HomeAssistant,
        entry: PathConfigEntry,
        source: str,
        fetch: Callable[[], Awaitable[Any]],
        seconds: int,
    ) -> None:
        self.source = source
        self.fetch = fetch
        self.seconds = seconds
        self.failures = 0
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"PATH {source}",
            update_interval=timedelta(seconds=seconds),
        )

    async def _async_update_data(self):
        try:
            data = await self.fetch()
        except (CannotConnect, InvalidFeed) as err:
            self.failures = min(self.failures + 1, 6)
            delay = min(self.seconds * 2**self.failures, max(self.seconds, 900))
            if isinstance(err, RateLimited):
                delay = max(delay, err.seconds)
            self.update_interval = timedelta(seconds=delay)
            raise UpdateFailed(
                translation_domain="path_rail", translation_key="update_failed"
            ) from err
        self.failures = 0
        self.update_interval = timedelta(seconds=self.seconds)
        return data
