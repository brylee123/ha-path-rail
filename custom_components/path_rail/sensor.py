"""Arrival boards and a feed-health diagnostic sensor."""

from datetime import UTC, datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, STATIONS
from .coordinator import PathConfigEntry, PathCoordinator
from .entity import PathBoardEntity, async_track_boards
from .service_sensor import create_service_sensors
from .source_health import create_source_health_sensors

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant, entry: PathConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        [
            PathFeedStatus(coordinator),
            *create_service_sensors(coordinator),
            *create_source_health_sensors(coordinator),
        ]
    )
    entry.async_on_unload(
        async_track_boards(
            coordinator,
            async_add_entities,
            lambda key: [
                PathArrivalSensor(coordinator, key, destination=True),
                PathCountdownSensor(coordinator, key, destination=True),
            ],
            destination=True,
        )
    )
    entry.async_on_unload(
        async_track_boards(
            coordinator,
            async_add_entities,
            lambda key: [
                PathArrivalSensor(coordinator, key),
                PathCountdownSensor(coordinator, key),
            ],
        )
    )


class PathArrivalSensor(PathBoardEntity, SensorEntity):
    """First arrival message in upstream order, with the full board attached."""

    _unrecorded_attributes = frozenset({"arrivals", "fetched_at"})

    def __init__(
        self, coordinator: PathCoordinator, key: tuple[str, str], *, destination: bool = False
    ) -> None:
        super().__init__(coordinator, key, "arrivals", destination=destination)

    @property
    def native_value(self) -> str | None:
        return self.board.arrivals[0].message if self.board and self.board.arrivals else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        board = self.board
        first = board.arrivals[0] if board and board.arrivals else None
        attributes = {
            "station_code": self.key[0],
            "station_name": STATIONS.get(self.key[0], self.key[0]),
            "arrivals": [item.as_dict() for item in self.board.arrivals] if self.board else [],
            "arrival_count": len(self.board.arrivals) if self.board else None,
            "fetched_at": self.coordinator.data.fetched_at.isoformat(),
            "color": first.colors[0] if first and len(first.colors) == 1 else None,
            "colors": list(first.colors) if first else [],
            "board_type": "destination" if self.destination else "direction",
        }
        if self.destination:
            attributes.update(
                destination_code=self.key[1],
                destination=board.name if board else self.key[1],
                source_directions=list(board.source_directions) if board else [],
            )
        else:
            attributes["direction"] = self.key[1]
        return attributes


class PathCountdownSensor(PathBoardEntity, SensorEntity):
    """Feed-reported seconds for the same first arrival, when it is timed."""

    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_suggested_unit_of_measurement = UnitOfTime.MINUTES
    _attr_suggested_display_precision = 1

    def __init__(
        self, coordinator: PathCoordinator, key: tuple[str, str], *, destination: bool = False
    ) -> None:
        super().__init__(coordinator, key, "countdown", destination=destination)

    @property
    def native_value(self) -> int | None:
        return self.board.arrivals[0].countdown if self.board and self.board.arrivals else None


class PathFeedStatus(CoordinatorEntity[PathCoordinator], SensorEntity):
    """Remain readable through an outage to explain board unavailability."""

    _attr_has_entity_name = True
    _attr_translation_key = "feed_status"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["ok", "stale", "missing_station", "empty", "error"]
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _unrecorded_attributes = frozenset(
        {"last_successful_fetch", "oldest_prediction_updated", "newest_prediction_updated"}
    )

    def __init__(self, coordinator: PathCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_feed_status"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "service_announcements")},
            name="PATH Service",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def available(self) -> bool:
        return True

    @property
    def native_value(self) -> str:
        if not self.coordinator.last_update_success:
            return "error"
        boards = self.coordinator.data.boards
        if any(
            station not in self.coordinator.data.stations for station in self.coordinator.stations
        ):
            return "missing_station"
        selected = [board for key, board in boards.items() if key[0] in self.coordinator.stations]
        if any(
            not board.fresh(datetime.now(UTC), self.coordinator.stale_after) for board in selected
        ):
            return "stale"
        if not any(board.arrivals for board in selected):
            return "empty"
        return "ok"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        timestamps = [
            item.updated
            for key, board in self.coordinator.data.boards.items()
            if key[0] in self.coordinator.stations
            for item in board.arrivals
            if item.updated is not None
        ]
        return {
            "oldest_prediction_updated": min(timestamps).isoformat() if timestamps else None,
            "newest_prediction_updated": max(timestamps).isoformat() if timestamps else None,
            "last_successful_fetch": self.coordinator.data.fetched_at.isoformat(),
            "consecutive_failures": self.coordinator.failures,
            "poll_interval_seconds": self.coordinator.update_interval.total_seconds(),
            "stale_after_seconds": self.coordinator.stale_after,
        }
