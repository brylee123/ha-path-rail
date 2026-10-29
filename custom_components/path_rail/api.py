"""Translate the independent RidePATH library's data for Home Assistant."""

import aiohttp
from panynj_ridepath import CannotConnect, RateLimited, RidePathClient

from .models import Feed, normalize_feed

__all__ = ["CannotConnect", "PathApi", "RateLimited"]


class PathApi:
    """Thin adapter: HTTP and response parsing live entirely in the library."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self.client = RidePathClient(session)

    async def async_fetch(self) -> Feed:
        return normalize_feed(await self.client.async_fetch())
