"""Thin adapter around the independent public-feed library."""

import aiohttp
from panynj_ridepath import RidePathClient

from .service_models import normalize_alerts, normalize_planned, normalize_site


class ServiceApi:
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self.client = RidePathClient(session)

    async def async_fetch_alerts(self):
        return normalize_alerts(await self.client.async_fetch_alerts())

    async def async_fetch_planned(self):
        return normalize_planned(await self.client.async_fetch_planned())

    async def async_fetch_site(self):
        return normalize_site(await self.client.async_fetch_site())
