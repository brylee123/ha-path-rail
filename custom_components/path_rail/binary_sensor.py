"""Expose only delays explicitly reported by the feed."""

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import PathConfigEntry, PathCoordinator
from .entity import PathBoardEntity, async_track_boards

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant, entry: PathConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    entry.async_on_unload(
        async_track_boards(
            coordinator,
            async_add_entities,
            lambda key: [PathReportedDelay(coordinator, key, destination=True)],
            destination=True,
        )
    )
    entry.async_on_unload(
        async_track_boards(
            coordinator,
            async_add_entities,
            lambda key: [PathReportedDelay(coordinator, key)],
        )
    )


class PathReportedDelay(PathBoardEntity, BinarySensorEntity):
    """On means at least one message literally says Delayed."""

    def __init__(
        self, coordinator: PathCoordinator, key: tuple[str, str], *, destination: bool = False
    ) -> None:
        super().__init__(coordinator, key, "reported_delay", destination=destination)

    @property
    def is_on(self) -> bool | None:
        if not self.board or not self.board.arrivals:
            return None
        return any(item.delayed for item in self.board.arrivals)
