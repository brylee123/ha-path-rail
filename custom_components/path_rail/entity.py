"""Shared station and availability handling."""

from collections.abc import Callable
from datetime import UTC, datetime

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DIRECTIONS, DOMAIN, STATION_LABELS, STATIONS
from .coordinator import PathCoordinator
from .models import Board, DestinationBoard


@callback
def async_track_boards(
    coordinator: PathCoordinator,
    async_add_entities: AddEntitiesCallback,
    factory: Callable[[tuple[str, str]], list[Entity]],
    *,
    destination: bool = False,
) -> Callable[[], None]:
    """Discover new direction boards on later polls as service changes."""
    known: set[tuple[str, str]] = set()

    @callback
    def discover() -> None:
        entities = []
        boards = coordinator.data.destination_boards if destination else coordinator.data.boards
        for key in boards:
            if key[0] in coordinator.stations and key not in known:
                known.add(key)
                entities.extend(factory(key))
        if entities:
            async_add_entities(entities)

    remove = coordinator.async_add_listener(discover)
    discover()
    return remove


class PathBoardEntity(CoordinatorEntity[PathCoordinator]):
    """A station/direction entity, unavailable on errors or stale source data."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PathCoordinator,
        key: tuple[str, str],
        kind: str,
        *,
        destination: bool = False,
    ) -> None:
        super().__init__(coordinator)
        self.key = key
        self.destination = destination
        self._last_destination_board = None
        station, direction = key
        self._attr_entity_registry_enabled_default = destination
        if destination:
            self._last_destination_board = coordinator.data.destination_boards[key]
            self._attr_unique_id = f"destination_{station}_{direction}_{kind}"
            self._attr_translation_key = f"destination_{kind}"
            self._attr_translation_placeholders = {
                "destination": STATION_LABELS.get(direction, direction)
            }
        else:
            self._attr_unique_id = f"{station}_{direction}_{kind}"
            self._attr_translation_key = (
                f"{kind}_{direction.lower()}" if direction in DIRECTIONS else kind
            )
            self._attr_translation_placeholders = {"direction": direction}
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, station)},
            name=f"PATH {STATIONS.get(station, station)}",
            manufacturer="Port Authority of New York and New Jersey",
            model="RidePATH arrival board",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def board(self) -> Board | DestinationBoard | None:
        if self.destination:
            data = self.coordinator.data
            board = data.destination_boards.get(self.key)
            if board is not None:
                self._last_destination_board = board
                return board
            # A rare service destination can disappear from a healthy response.
            # Keep its entity, but never reuse a previous train or countdown.
            if previous := self._last_destination_board:
                return DestinationBoard(
                    previous.station,
                    previous.target,
                    previous.name,
                    (),
                    previous.source_directions,
                    any(
                        (previous.station, direction) in data.boards
                        for direction in previous.source_directions
                    ),
                )
            return None
        return self.coordinator.data.boards.get(self.key)

    @property
    def available(self) -> bool:
        return (
            super().available
            and self.key[0] in self.coordinator.stations
            and self.board is not None
            and self.board.fresh(datetime.now(UTC), self.coordinator.stale_after)
        )
