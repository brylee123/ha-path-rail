"""Home Assistant announcement grouping and explicitly inferred line status."""

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from html.parser import HTMLParser
from typing import Any
from zoneinfo import ZoneInfo

from panynj_ridepath.announcements import AnnouncementFeed, SiteFeed

from .const import LINE_STATIONS
from .models import InvalidFeed
from .site_calendar import CALENDAR_END, CALENDAR_START, US_HOLIDAYS

LINE_IDS = ("red", "yellow", "green", "blue", "night-yellow")
LINE_NAMES = {
    "red": "Newark–World Trade Center",
    "yellow": "Journal Square–33rd Street",
    "green": "Hoboken–World Trade Center",
    "blue": "Hoboken–33rd Street",
    "night-yellow": "Journal Square–33rd Street via Hoboken",
}
DAY_LINES = frozenset({"red", "yellow", "green", "blue"})
NIGHT_LINES = frozenset({"red", "night-yellow"})
_ALIASES = {
    "NWK-WTC": "red",
    "WTC-NWK": "red",
    "HOB-WTC": "green",
    "WTC-HOB": "green",
    "JSQ-33": "yellow",
    "33-JSQ": "yellow",
    "JSQ-33S": "yellow",
    "33S-JSQ": "yellow",
    "HOB-33": "blue",
    "33-HOB": "blue",
    "HOB-33S": "blue",
    "33S-HOB": "blue",
}
_ROUTE = re.compile(
    r"\b(?:JSQ-33S?(?:\s+St\.?)?\s+(?:\(\s*)?via\s+HOB(?:\s*\))?|"
    r"33S?-JSQ\s+(?:\(\s*)?via\s+HOB(?:\s*\))?|"
    + "|".join(sorted(map(re.escape, _ALIASES), key=len, reverse=True))
    + r")\b",
    re.IGNORECASE,
)
_STATION = re.compile(r"(?<!-)\b(NWK|HAR|JSQ|GRV|NEW|EXP|HOB|WTC|CHR|09S|14S|23S|33S)\b(?!-)")
_STATUS = re.compile(
    r"\b(?:not\s+running|not\s+delayed|no\s+delays|no\s+longer\s+suspended|not\s+suspended|"
    r"resum(?:ing|ed)\s+normal\s+service|normal\s+service|running|"
    r"suspended|suspension|no\s+(?:train\s+)?service|delayed|delays(?:\s+continue)?)\b",
    re.IGNORECASE,
)
_NY = ZoneInfo("America/New_York")
_HOLIDAYS = tuple(
    (datetime.fromisoformat(start), datetime.fromisoformat(end)) for start, end in US_HOLIDAYS
)


def _route_matches(text: str):
    for match in _ROUTE.finditer(text):
        raw = match.group().upper()
        yield match, "night-yellow" if "VIA" in raw else _ALIASES[raw]


def _category(record: dict[str, Any]) -> str:
    all_fields = " ".join(
        str(record.get(key) or "") for key in ("TemplateName", "Subject", "SentMessage")
    )
    for category in ("elevator", "escalator"):
        if re.search(category, all_fields, re.IGNORECASE):
            return category
    headings = " ".join(str(record.get(key) or "") for key in ("TemplateName", "Subject"))
    if re.search("Mechanical", headings, re.IGNORECASE):
        return "mechanical"
    if re.search("Service|Delay", headings, re.IGNORECASE):
        return "service"
    return "other"


@dataclass(frozen=True)
class Alert:
    incident_id: str
    message_id: str
    timestamp: datetime
    subject: str
    message: str
    template: str
    state: str
    category: str
    stations: tuple[str, ...]
    lines_mentioned: tuple[str, ...]

    @property
    def active(self) -> bool:
        # Match the site's exact explicit Closed marker, without translating it.
        return self.state != "Closed"

    @property
    def accessibility(self) -> bool:
        return self.category in {"elevator", "escalator"}

    def as_dict(self) -> dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "message_id": self.message_id,
            "sent_at": self.timestamp.isoformat(),
            "subject": self.subject,
            "message": self.message,
            "template_name": self.template,
            "source_state": self.state,
            "active": self.active,
            "category": self.category,
            "stations": list(self.stations),
            "lines_mentioned": list(self.lines_mentioned),
            "related_stations": sorted(
                set(self.stations).union(
                    *(LINE_STATIONS.get(line, ()) for line in self.lines_mentioned)
                )
            ),
            "unscoped": not self.stations and not self.lines_mentioned,
        }


@dataclass(frozen=True)
class AlertSnapshot:
    alerts: tuple[Alert, ...]
    fetched_at: datetime


def normalize_alerts(feed: AnnouncementFeed) -> AlertSnapshot:
    latest: dict[str, Alert] = {}
    for record in feed.records:
        raw_timestamp = record.get("sentdate2")
        match = re.fullmatch(r"/Date\((\d+)(?:[+-]\d{4})?\)/", str(raw_timestamp))
        if not match:
            raise InvalidFeed("Alert has no usable incident timestamp")
        try:
            timestamp = datetime.fromtimestamp(int(match.group(1)) / 1000, UTC)
        except (ValueError, OverflowError, OSError) as err:
            raise InvalidFeed("Invalid alert timestamp") from err
        message_id = str(record["messageid"])
        incident = (
            f"ebid:{record['ebid']}" if record.get("ebid") is not None else f"mid:{message_id}"
        )
        message = record["SentMessage"]
        template = str(record.get("TemplateName") or "")
        state = record.get("state")
        if not isinstance(state, str) or not state:
            raise InvalidFeed("Alert is missing its source state")
        alert = Alert(
            incident,
            message_id,
            timestamp,
            record["Subject"],
            message,
            template,
            state,
            _category(record),
            tuple(sorted(set(_STATION.findall(template + " " + message)))),
            tuple(sorted({line for _, line in _route_matches(message)})),
        )
        if incident not in latest or timestamp >= latest[incident].timestamp:
            latest[incident] = alert
    return AlertSnapshot(
        tuple(sorted(latest.values(), key=lambda item: item.timestamp, reverse=True)),
        feed.fetched_at,
    )


class _PlainText(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skip = 0
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.skip += 1
        elif tag in {"p", "div", "br", "li", "h1", "h2", "h3"}:
            self.parts.append("\n")
        elif tag == "a":
            href = dict(attrs).get("href")
            if isinstance(href, str) and href.startswith(("https://", "http://")):
                self.links.append(href)

    def handle_endtag(self, tag):
        if tag in {"script", "style"} and self.skip:
            self.skip -= 1
        elif tag in {"p", "div", "li"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def plain_text(value: str) -> str:
    parser = _PlainText()
    parser.feed(value)
    return "\n".join(line.strip() for line in "".join(parser.parts).splitlines() if line.strip())


def _metadata(entity: dict, keys: tuple[str, ...]):
    props = entity.get("properties", {})
    for item in (entity, props, props.get("metadata"), props.get("contentFragment")):
        if isinstance(item, dict):
            for key in keys:
                if item.get(key) not in (None, ""):
                    return item[key]
    return None


@dataclass(frozen=True)
class PlannedSnapshot:
    notices: tuple[dict[str, Any], ...]
    fetched_at: datetime


def normalize_planned(feed: AnnouncementFeed) -> PlannedSnapshot:
    notices = []
    for entity in feed.records:
        action = _metadata(
            entity, ("cq:lastReplicationAction", "lastReplicationAction", "replicationAction")
        )
        status = _metadata(
            entity,
            (
                "cq:lastReplicationStatus",
                "lastReplicationStatus",
                "replicationStatus",
                "publicationStatus",
                "status",
            ),
        )
        if action:
            if str(action).lower() != "activate":
                continue
        elif status and str(status).lower() in {
            "deactivate",
            "deactivated",
            "unpublish",
            "unpublished",
            "not_published",
        }:
            continue
        props = entity["properties"]
        elements = props["elements"]

        def value(key):
            element = elements.get(key, {})
            return element.get("value") if isinstance(element, dict) else None

        title = value("title") or props.get("title") or props.get("name")
        description = value("description")
        if not isinstance(title, str) or not isinstance(description, str):
            raise InvalidFeed("Planned notice has no title/description")
        parser = _PlainText()
        html = elements["description"].get(":type") == "text/html"
        if html:
            parser.feed(description)
        notices.append(
            {
                "id": props.get("name"),
                "title": title,
                "description": plain_text(description) if html else description,
                "links": list(dict.fromkeys(parser.links)),
                "modified": props.get("modified"),
                "section": "Service Changes",
            }
        )
    return PlannedSnapshot(tuple(notices), feed.fetched_at)


@dataclass(frozen=True)
class SiteSnapshot:
    windows: dict[str, int]
    lines: dict[str, dict]
    fetched_at: datetime

    def scheduled_lines(self, now: datetime) -> frozenset[str] | None:
        if not datetime.fromisoformat(CALENDAR_START) <= now < datetime.fromisoformat(CALENDAR_END):
            return None
        local = now.astimezone(_NY)
        holiday = any(start <= now < end for start, end in _HOLIDAYS)
        period = "weekend" if local.weekday() >= 5 or holiday else "weekday"
        minute = local.hour * 60 + local.minute
        day = self.windows[period + "DayStart"] <= minute < self.windows[period + "DayEnd"]
        return DAY_LINES if day else NIGHT_LINES


def normalize_site(feed: SiteFeed) -> SiteSnapshot:
    widgets = []

    def walk(node):
        if not isinstance(node, dict):
            return
        if node.get(":type") == "portauthority/components/PATripPlanner":
            widgets.append(node)
        children = node.get(":items", {})
        if isinstance(children, dict):
            for child in children.values():
                walk(child)

    walk(feed.page_model)
    if len(widgets) != 1:
        raise InvalidFeed("Expected one live PATH trip-planner widget")
    if widgets[0].get("configJson") != "/content/dam/path/trip-planner/trip-planner-config.json":
        raise InvalidFeed("The PATH site changed its configuration source")
    windows = {}
    for key in ("weekdayDayStart", "weekdayDayEnd", "weekendDayStart", "weekendDayEnd"):
        value = widgets[0].get(key)
        if not isinstance(value, str) or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", value):
            raise InvalidFeed("Invalid PATH service window")
        hour, minute = map(int, value.split(":"))
        windows[key] = hour * 60 + minute
    if any(
        windows[period + "DayStart"] >= windows[period + "DayEnd"]
        for period in ("weekday", "weekend")
    ):
        raise InvalidFeed("Unsupported PATH service window")
    lines = feed.config.get("lines")
    if not isinstance(lines, dict) or any(
        not isinstance(lines.get(key), dict)
        or lines[key].get("id") != key
        or not isinstance(lines[key].get("stops"), list)
        for key in LINE_IDS
    ):
        raise InvalidFeed("Unsupported PATH line configuration")
    return SiteSnapshot(windows, lines, feed.fetched_at)


def alert_effects(alert: Alert) -> dict[str, str | None]:
    """Associate route mentions with their clause, never all lines in a message."""
    if alert.accessibility or not alert.active:
        return {}
    effects: dict[str, str | None] = {}
    for clause in re.split(r"(?<=[.!?;])\s+|\n+", alert.message):
        if re.search(
            r"\b(?:tomorrow|tonight|will\s+be|starting|beginning|scheduled\s+for|may|might|could|possible|expected|anticipated)\b",
            clause,
            re.IGNORECASE,
        ):
            continue
        since = 0
        subjects = set()
        for status in _STATUS.finditer(clause):
            routes = {line for _, line in _route_matches(clause[since : status.start()])}
            subjects = routes or subjects
            phrase = status.group().lower()
            if phrase in {
                "not delayed",
                "no delays",
                "no longer suspended",
                "not suspended",
                "running",
                "normal service",
            } or phrase.startswith("resum"):
                effect = "good_service"
            elif phrase in {"suspended", "suspension", "not running"} or phrase.startswith("no "):
                effect = "suspended"
            else:
                effect = "delayed"
            for line in subjects:
                effects[line] = effect
            since = status.end()
    for line in alert.lines_mentioned:
        effects.setdefault(line, None)
    return effects


def line_status(line: str, alerts: AlertSnapshot, site: SiteSnapshot, now: datetime) -> str | None:
    effects = []
    ambiguous_system_notice = False
    for alert in alerts.alerts:
        if not alert.active or alert.accessibility:
            continue
        classified = alert_effects(alert)
        if not alert.lines_mentioned:
            # An active non-accessibility notice could affect any route. Do not
            # turn incomplete natural-language extraction into an all-clear.
            ambiguous_system_notice = True
        if line in classified:
            effects.append(classified[line])
    for severity in ("suspended", "delayed"):
        if severity in effects:
            return severity
    scheduled = site.scheduled_lines(now)
    if scheduled is None or ambiguous_system_notice or None in effects:
        return None
    return "good_service" if line in scheduled else "not_scheduled"
