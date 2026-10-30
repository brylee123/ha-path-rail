"""Readable source health and successful-fetch timestamps, including outages."""

from datetime import datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import EntityCategory
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


class SourceHealthEntity(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, source: str, kind: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{source}_{kind}"
        self._attr_translation_key = f"{source}_{kind}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "service_announcements")},
            name="PATH Service",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def available(self) -> bool:
        # A failed feed must not hide its diagnostic state or last success.
        return True


class SourceStatusSensor(SourceHealthEntity):
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["ok", "error"]
    _unrecorded_attributes = frozenset({"last_successful_fetch"})

    def __init__(self, coordinator, source: str) -> None:
        super().__init__(coordinator, source, "source_status")

    @property
    def native_value(self) -> str:
        return (
            "ok"
            if self.coordinator.last_update_success and self.coordinator.data is not None
            else "error"
        )

    @property
    def extra_state_attributes(self) -> dict:
        data = self.coordinator.data
        return {
            "last_successful_fetch": data.fetched_at.isoformat() if data else None,
            "consecutive_failures": self.coordinator.failures,
            "poll_interval_seconds": self.coordinator.update_interval.total_seconds(),
            "normal_poll_interval_seconds": self.coordinator.seconds,
        }


class SourceFetchSensor(SourceHealthEntity):
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator, source: str) -> None:
        super().__init__(coordinator, source, "last_successful_fetch")

    @property
    def native_value(self) -> datetime | None:
        data = self.coordinator.data
        return data.fetched_at if data else None


def create_source_health_sensors(arrivals) -> list[SensorEntity]:
    sources = {"arrivals": arrivals, **arrivals.services}
    return [
        *(SourceStatusSensor(source, key) for key, source in arrivals.services.items()),
        *(SourceFetchSensor(source, key) for key, source in sources.items()),
    ]
