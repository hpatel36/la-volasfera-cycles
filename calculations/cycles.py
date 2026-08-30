"""Project True Node station events onto direct and converse timelines."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from calculations.node_stations import NodeStation, as_utc, find_true_node_stations_near


PROGRESSION_FACTORS = {
    "transit": 1.0,
    "secondary": 365.242199074074,
    "tertiary": 29.530588857,
    "minor": 12.368266432,
}


@dataclass(frozen=True)
class CycleEvent:
    mode: str
    projected_dt_utc: datetime
    source_station: NodeStation


def source_anchor_for_target(
    reference_utc: datetime,
    target_utc: datetime,
    *,
    factor: float,
    converse: bool,
) -> datetime:
    """Invert a cycle projection to find the source date near a target date."""
    reference_utc = as_utc(reference_utc)
    target_utc = as_utc(target_utc)
    source_delta = (target_utc - reference_utc) / factor
    return reference_utc - source_delta if converse else reference_utc + source_delta


def project_station(
    reference_utc: datetime,
    station_utc: datetime,
    *,
    factor: float,
    converse: bool,
) -> datetime:
    """Project one source station onto a cycle timeline."""
    reference_utc = as_utc(reference_utc)
    station_utc = as_utc(station_utc)
    source_delta = station_utc - reference_utc
    projected_delta = -source_delta * factor if converse else source_delta * factor
    return reference_utc + projected_delta


def generate_cycle_events(
    reference_utc: datetime,
    anchor_utc: datetime,
    *,
    method: str,
    converse: bool,
    before: int = 4,
    after: int = 4,
) -> list[CycleEvent]:
    """Calculate and project stations surrounding an anchor on one timeline."""
    try:
        factor = PROGRESSION_FACTORS[method]
    except KeyError as error:
        raise ValueError(f"unknown cycle method: {method}") from error

    reference_utc = as_utc(reference_utc)
    anchor_utc = as_utc(anchor_utc)
    source_anchor = source_anchor_for_target(
        reference_utc,
        anchor_utc,
        factor=factor,
        converse=converse,
    )
    source_before = after if converse else before
    source_after = before if converse else after
    stations = find_true_node_stations_near(
        source_anchor,
        before=source_before,
        after=source_after,
    )
    mode = f"{method}_{'converse' if converse else 'direct'}"
    events = [
        CycleEvent(
            mode=mode,
            projected_dt_utc=project_station(
                reference_utc,
                station.dt_utc,
                factor=factor,
                converse=converse,
            ),
            source_station=station,
        )
        for station in stations
    ]
    events.sort(key=lambda event: event.projected_dt_utc)
    earlier = [event for event in events if event.projected_dt_utc < anchor_utc]
    later = [event for event in events if event.projected_dt_utc >= anchor_utc]
    return earlier[-before:] + later[:after]
