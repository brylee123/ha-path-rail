"""UI setup and options for PATH Rail."""

from typing import Any

import probatio
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig, SelectSelectorMode

from .api import CannotConnect, PathApi
from .const import (
    CONF_STALE_AFTER,
    CONF_STATIONS,
    DEFAULT_STALE_AFTER,
    DOMAIN,
    NAME,
    STATIONS,
)
from .models import InvalidFeed


def _schema(settings: dict[str, Any]) -> probatio.Schema:
    return probatio.Schema(
        {
            probatio.Required(
                CONF_STATIONS, default=settings.get(CONF_STATIONS, ["JSQ"])
            ): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        {"value": code, "label": f"{name} ({code})"}
                        for code, name in STATIONS.items()
                    ],
                    multiple=True,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            probatio.Required(
                CONF_STALE_AFTER, default=settings.get(CONF_STALE_AFTER, DEFAULT_STALE_AFTER)
            ): probatio.All(probatio.Coerce(int), probatio.Range(min=120, max=1800)),
        }
    )


def _errors(settings: dict[str, Any]) -> dict[str, str]:
    if not settings[CONF_STATIONS]:
        return {CONF_STATIONS: "select_station"}
    return {}


class PathFlow(ConfigFlow, domain=DOMAIN):
    """Create a single global feed entry with selectable stations."""

    VERSION = 2

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        errors = {}
        if user_input is not None:
            errors = _errors(user_input)
            if not errors:
                try:
                    feed = await PathApi(async_get_clientsession(self.hass)).async_fetch()
                except CannotConnect:
                    errors["base"] = "cannot_connect"
                except InvalidFeed:
                    errors["base"] = "invalid_feed"
                else:
                    if not set(user_input[CONF_STATIONS]).intersection(feed.stations):
                        errors[CONF_STATIONS] = "station_missing"
                    else:
                        return self.async_create_entry(title=NAME, data=user_input)
        return self.async_show_form(
            step_id="user", data_schema=_schema(user_input or {}), errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return PathOptionsFlow()


class PathOptionsFlow(OptionsFlow):
    """Change stations and freshness limits without editing YAML."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors = {}
        if user_input is not None:
            errors = _errors(user_input)
            if not errors:
                return self.async_create_entry(title="", data=user_input)
        settings = user_input or {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(step_id="init", data_schema=_schema(settings), errors=errors)
