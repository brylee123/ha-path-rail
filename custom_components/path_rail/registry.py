"""Consolidate line devices and shorten automatically assigned entity IDs."""

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN, LINE_LABELS


@callback
def async_prepare_registry(hass: HomeAssistant, entry) -> set[tuple[str, str]]:
    registry = er.async_get(hass)
    devices = dr.async_get(hass)
    candidates = set()
    line_ids = {f"{DOMAIN}_line_{line}_status" for line in LINE_LABELS}
    for entity in er.async_entries_for_config_entry(registry, entry.entry_id):
        if entity.platform != DOMAIN:
            continue
        renamed = (
            entity.unique_id in line_ids
            or entity.unique_id.startswith("destination_")
            or any(
                entity.unique_id.endswith(f"_{kind}") and "_To" in entity.unique_id
                for kind in ("arrivals", "countdown", "reported_delay")
            )
        )
        if (
            renamed
            and entity.name is None
            and registry.async_regenerate_entity_id(entity) == entity.entity_id
        ):
            candidates.add((entity.domain, entity.unique_id))
    shared = devices.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, "line_status")},
        name="PATH Line Status",
        entry_type=dr.DeviceEntryType.SERVICE,
    )
    for entity in er.async_entries_for_config_entry(registry, entry.entry_id):
        if (
            entity.platform == DOMAIN
            and entity.unique_id in line_ids
            and entity.device_id != shared.id
        ):
            registry.async_update_entity(entity.entity_id, device_id=shared.id)
    old_identifiers = {(DOMAIN, f"line_{line}") for line in LINE_LABELS}
    for device in list(dr.async_entries_for_config_entry(devices, entry.entry_id)):
        if (
            device.id != shared.id
            and device.identifiers & old_identifiers
            and not er.async_entries_for_device(registry, device.id)
        ):
            devices.async_remove_device(device.id)
    return candidates


@callback
def async_finish_registry(hass: HomeAssistant, candidates: set[tuple[str, str]]) -> None:
    registry = er.async_get(hass)
    for domain, unique_id in candidates:
        if entity_id := registry.async_get_entity_id(domain, DOMAIN, unique_id):
            entity = registry.async_get(entity_id)
            new_id = registry.async_regenerate_entity_id(entity)
            if new_id != entity_id:
                registry.async_update_entity(entity_id, new_entity_id=new_id)
