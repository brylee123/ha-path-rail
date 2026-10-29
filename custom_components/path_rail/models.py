"""Validated feed models. This module does not depend on Home Assistant."""

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from panynj_ridepath.models import Feed as SourceFeed
from panynj_ridepath.models import InvalidFeed as InvalidFeed
from panynj_ridepath.models import parse_response


def _timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return result.astimezone(UTC) if result.tzinfo else None


def _seconds(value: Any) -> int | None:
    # The observed feed uses strings; accept JSON integers, but never booleans,
    # negative values, fractional values, or non-numeric status text.
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if 0 <= value <= 604800 else None
    if isinstance(value, str) and re.fullmatch(r"[0-9]{1,6}", value):
        number = int(value)
        return number if number <= 604800 else None
    return None


@dataclass(frozen=True)
class Arrival:
    target: str
    seconds: int | None
    message: str
    color: str | None
    headsign: str | None
    updated: datetime | None

    @property
    def delayed(self) -> bool:
        """Only an explicit upstream report means delayed."""
        return self.message.casefold() == "delayed"

    @property
    def countdown(self) -> int | None:
        """Do not present a time estimate for non-countdown status messages."""
        return self.seconds if re.fullmatch(r"[0-9]+ min", self.message) else None

    def as_dict(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "seconds_to_arrival": self.seconds,
            "arrival_time_message": self.message,
            "line_color": self.color,
            "head_sign": self.headsign,
            "last_updated": self.updated.isoformat() if self.updated else None,
            "reported_delayed": self.delayed,
        }


@dataclass(frozen=True)
class Board:
    station: str
    direction: str
    arrivals: tuple[Arrival, ...]

    def fresh(self, now: datetime, stale_after: int) -> bool:
        # Empty arrays are valid responses, but have no source freshness proof.
        # Do not reuse the prior board's trains or timestamps.
        return all(
            item.updated is not None and -60 <= (now - item.updated).total_seconds() <= stale_after
            for item in self.arrivals
        )


@dataclass(frozen=True)
class Feed:
    boards: dict[tuple[str, str], Board]
    stations: tuple[str, ...]
    fetched_at: datetime


def normalize_feed(source: SourceFeed) -> Feed:
    """Apply Home Assistant display policy to source-shaped library data."""
    boards = {}
    for station in source.results:
        for destination in station.destinations:
            arrivals = []
            for message in destination.messages:
                color = message.lineColor
                headsign = message.headSign
                arrivals.append(
                    Arrival(
                        target=message.target,
                        seconds=_seconds(message.secondsToArrival),
                        message=message.arrivalTimeMessage,
                        color=color
                        if isinstance(color, str)
                        and re.fullmatch(r"[0-9a-fA-F]{6}(?:,[0-9a-fA-F]{6})*", color)
                        else None,
                        headsign=headsign
                        if isinstance(headsign, str) and len(headsign) <= 255
                        else None,
                        updated=_timestamp(message.lastUpdated),
                    )
                )
            key = (station.consideredStation, destination.label)
            boards[key] = Board(*key, tuple(arrivals))
    return Feed(
        boards, tuple(station.consideredStation for station in source.results), source.fetched_at
    )


def parse_feed(payload: Any, fetched_at: datetime) -> Feed:
    """Adapter entry point for fixtures and callers with an existing JSON body."""
    return normalize_feed(parse_response(payload, fetched_at))
