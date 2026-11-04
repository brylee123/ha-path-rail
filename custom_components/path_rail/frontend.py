"""Serve and register the bundled PATH arrival card."""

from pathlib import Path
from urllib.parse import urlsplit

from homeassistant.components import frontend
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace import LOVELACE_DATA
from homeassistant.components.lovelace.resources import ResourceStorageCollection
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration
from homeassistant.util.hass_dict import HassKey

from .const import DOMAIN

CARD_FILENAME = "path-rail-arrivals-card.js"
CARD_URL = f"/{DOMAIN}/{CARD_FILENAME}"
LEGACY_CARD_PATHS = {
    f"/hacsfiles/path-rail-arrivals-card/{CARD_FILENAME}",
    f"/local/{CARD_FILENAME}",
}
DATA_EXTRA_CARD_URL: HassKey[str] = HassKey(f"{DOMAIN}_extra_card_url")


def _is_card_resource(url: str, *, include_legacy: bool = False) -> bool:
    """Only manage known local resources; leave remote/custom URLs alone."""
    parsed = urlsplit(url)
    return not (parsed.scheme or parsed.netloc) and (
        parsed.path == CARD_URL or (include_legacy and parsed.path in LEGACY_CARD_PATHS)
    )


async def async_setup_static_path(hass: HomeAssistant) -> None:
    """Register the packaged module once for the lifetime of the integration."""
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL, str(Path(__file__).parent / "www" / CARD_FILENAME), False)]
    )


async def async_register_card(hass: HomeAssistant) -> None:
    """Create or migrate the dashboard module without duplicate registrations."""
    integration = await async_get_integration(hass, DOMAIN)
    url = f"{CARD_URL}?v={integration.version}"
    resources = hass.data[LOVELACE_DATA].resources
    if not isinstance(resources, ResourceStorageCollection):
        # YAML resources belong to the user. The supported frontend module hook
        # also loads the card in YAML mode without rewriting configuration files.
        if hass.data.get(DATA_EXTRA_CARD_URL) != url:
            if previous := hass.data.get(DATA_EXTRA_CARD_URL):
                frontend.remove_extra_js_url(hass, previous)
            frontend.add_extra_js_url(hass, url)
            hass.data[DATA_EXTRA_CARD_URL] = url
        return

    # This public API ensures lazy resource storage is loaded before inspecting it.
    await resources.async_get_info()
    matches = [
        item
        for item in resources.async_items()
        if _is_card_resource(item["url"], include_legacy=True)
    ]
    if not matches:
        await resources.async_create_item({"res_type": "module", "url": url})
        return

    # Prefer the bundled resource, retaining its ID when older copies also exist.
    primary = next((item for item in matches if _is_card_resource(item["url"])), matches[0])
    if primary["url"] != url or primary["type"] != "module":
        await resources.async_update_item(primary["id"], {"res_type": "module", "url": url})
    for item in matches:
        if item["id"] != primary["id"]:
            await resources.async_delete_item(item["id"])


async def async_remove_card(hass: HomeAssistant) -> None:
    """Remove our module registration when the integration entry is deleted."""
    if url := hass.data.pop(DATA_EXTRA_CARD_URL, None):
        frontend.remove_extra_js_url(hass, url)
    if (lovelace := hass.data.get(LOVELACE_DATA)) is None:
        return
    resources = lovelace.resources
    if isinstance(resources, ResourceStorageCollection):
        await resources.async_get_info()
        for item in list(resources.async_items()):
            if _is_card_resource(item["url"]):
                await resources.async_delete_item(item["id"])
