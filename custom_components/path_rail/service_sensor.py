"""Announcement lists and conservative, explicitly inferred line statuses."""

from datetime import UTC, datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, LINE_LABELS
from .service_coordinator import ServiceCoordinator
from .service_models import LINE_IDS, LINE_NAMES, line_status


class AnnouncementSensor(CoordinatorEntity[ServiceCoordinator], SensorEntity):
    _attr_has_entity_name = True
    _unrecorded_attributes = frozenset({"announcements", "fetched_at"})

    def __init__(self, coordinator: ServiceCoordinator, kind: str) -> None:
        super().__init__(coordinator)
        self.kind = kind
        self._attr_unique_id = f"{DOMAIN}_{kind}"
        self._attr_translation_key = kind
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "service_announcements")},
            name="PATH Service",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data is not None

    @property
    def items(self) -> list[dict[str, Any]]:
        data = self.coordinator.data
        if data is None:
            return []
        if self.kind == "planned_services":
            return list(data.notices)
        return [
            alert.as_dict()
            for alert in data.alerts
            if self.kind != "accessibility_alerts" or alert.accessibility
        ]

    @property
    def native_value(self) -> int | None:
        return len(self.items) if self.coordinator.data is not None else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "announcements": self.items,
            "active_count": sum(item.get("active", False) for item in self.items)
            if self.kind != "planned_services"
            else None,
            "section": {
                "service_alerts": "Alerts",
                "accessibility_alerts": "Elevators & Escalators",
                "planned_services": "Service Changes",
            }[self.kind],
            "fetched_at": self.coordinator.data.fetched_at.isoformat()
            if self.coordinator.data
            else None,
        }


class LineStatusSensor(CoordinatorEntity[ServiceCoordinator], SensorEntity):
    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["delayed", "suspended", "good_service", "not_scheduled"]
    _attr_translation_key = "line_status"
    _unrecorded_attributes = frozenset(
        {"announcements", "alerts_fetched_at", "timetable_fetched_at"}
    )

    def __init__(self, alerts: ServiceCoordinator, site: ServiceCoordinator, line: str) -> None:
        super().__init__(alerts)
        self.site = site
        self.line = line
        self._attr_unique_id = f"{DOMAIN}_line_{line}_status"
        self._attr_translation_placeholders = {"line": LINE_LABELS[line]}
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "line_status")},
            name="PATH Line Status",
            entry_type=DeviceEntryType.SERVICE,
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(self.site.async_add_listener(self._handle_coordinator_update))

    @property
    def available(self) -> bool:
        return (
            super().available
            and self.coordinator.data is not None
            and self.site.last_update_success
            and self.site.data is not None
        )

    @property
    def native_value(self) -> str | None:
        if not self.coordinator.data or not self.site.data:
            return None
        return line_status(self.line, self.coordinator.data, self.site.data, datetime.now(UTC))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        alerts, site = self.coordinator.data, self.site.data
        scheduled = site.scheduled_lines(datetime.now(UTC)) if site else None
        return {
            "line_id": self.line,
            "line_name": LINE_NAMES[self.line],
            "status_inferred": True,
            "status_basis": "Active incident messages plus PATH website service windows; Good Service means no identified active disruption for a scheduled line.",
            "scheduled": self.line in scheduled if scheduled is not None else None,
            "announcements": [
                item.as_dict() for item in alerts.alerts if self.line in item.lines_mentioned
            ]
            if alerts
            else [],
            "alerts_fetched_at": alerts.fetched_at.isoformat() if alerts else None,
            "timetable_fetched_at": site.fetched_at.isoformat() if site else None,
            "timetable_windows_minutes": site.windows if site else None,
        }


def create_service_sensors(arrivals) -> list[SensorEntity]:
    alerts, planned, site = (arrivals.services[key] for key in ("alerts", "planned", "site"))
    return [
        AnnouncementSensor(alerts, "service_alerts"),
        AnnouncementSensor(alerts, "accessibility_alerts"),
        AnnouncementSensor(planned, "planned_services"),
        *(LineStatusSensor(alerts, site, line) for line in LINE_IDS),
    ]
