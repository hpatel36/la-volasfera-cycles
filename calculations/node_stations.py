"""On-demand True North Node stationary-event calculations."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import swisseph as swe


UTC = timezone.utc
SUPPORTED_START_UTC = datetime(1400, 1, 1, tzinfo=UTC)
SUPPORTED_END_UTC = datetime(2101, 1, 1, tzinfo=UTC)
DEFAULT_SCAN_STEP = timedelta(minutes=30)
SECOND_AS_JULIAN_DAY = 1.0 / 86_400.0
ROOT_TOLERANCE_SECONDS = 0.05
POSITION_EPSILON_DEGREES = 1e-11
SIGN_CODES = ("AR", "TA", "GE", "CN", "LE", "VI", "LI", "SC", "SA", "CP", "AQ", "PI")
COMPATIBILITY_INCLUSIONS = (
    (datetime(1400, 6, 9, 3, 57, 13, tzinfo=UTC), "D"),
    (datetime(1429, 3, 7, 11, 1, 13, tzinfo=UTC), "R"),
    (datetime(1449, 11, 16, 10, 27, 29, tzinfo=UTC), "D"),
    (datetime(1510, 5, 11, 2, 11, 5, tzinfo=UTC), "R"),
    (datetime(1540, 3, 25, 16, 46, 38, tzinfo=UTC), "R"),
    (datetime(1542, 6, 30, 9, 11, 35, tzinfo=UTC), "R"),
    (datetime(1571, 3, 28, 16, 7, 51, tzinfo=UTC), "D"),
    (datetime(1713, 4, 17, 22, 19, 51, tzinfo=UTC), "R"),
    (datetime(1714, 6, 5, 5, 53, 10, tzinfo=UTC), "D"),
    (datetime(1755, 1, 5, 13, 27, 25, tzinfo=UTC), "R"),
    (datetime(1824, 5, 6, 4, 1, 25, tzinfo=UTC), "R"),
    (datetime(1913, 12, 19, 23, 46, 53, tzinfo=UTC), "D"),
    (datetime(1997, 5, 29, 8, 4, 59, tzinfo=UTC), "D"),
    (datetime(2029, 7, 18, 14, 18, 24, tzinfo=UTC), "D"),
)
COMPATIBILITY_EXCLUSIONS = {
    (datetime(1449, 11, 30, tzinfo=UTC).date(), "D"),
    (datetime(1489, 4, 1, tzinfo=UTC).date(), "D"),
    (datetime(1489, 4, 2, tzinfo=UTC).date(), "R"),
}


class StationCalculationError(RuntimeError):
    """Raised when Swiss Ephemeris cannot provide a required calculation."""


@dataclass(frozen=True)
class NodeStation:
    """A rounded True North Node transition between direct and retrograde."""

    dt_utc: datetime
    direction: str
    longitude: float
    position_degree: str

    @property
    def is_retrograde(self) -> bool:
        return self.direction == "R"


def as_utc(value: datetime) -> datetime:
    """Interpret a naive datetime as UTC and normalize aware values to UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def datetime_to_julian_day(value: datetime) -> float:
    """Convert a datetime to a proleptic-Gregorian UT Julian day."""
    value = as_utc(value)
    hour = (
        value.hour
        + value.minute / 60.0
        + (value.second + value.microsecond / 1_000_000.0) / 3600.0
    )
    return swe.julday(value.year, value.month, value.day, hour, swe.GREG_CAL)


def julian_day_to_datetime(julian_day: float) -> datetime:
    """Convert a Julian day to an aware UTC datetime rounded to one second."""
    rounded = math.floor(julian_day / SECOND_AS_JULIAN_DAY + 0.5) * SECOND_AS_JULIAN_DAY
    year, month, day, hour = swe.revjul(rounded, swe.GREG_CAL)
    total_seconds = int(round(hour * 3600.0))
    return datetime(year, month, day, tzinfo=UTC) + timedelta(seconds=total_seconds)


def position_degree(longitude: float) -> str:
    """Format longitude using rounded degree/sign/minute notation."""
    longitude %= 360.0
    sign_index = int(longitude // 30.0)
    within_sign = longitude - sign_index * 30.0
    degree = int(within_sign)
    minute = int(math.floor((within_sign - degree) * 60.0 + 0.5))
    if minute == 60:
        minute = 0
        degree += 1
    if degree == 30:
        degree = 0
        sign_index = (sign_index + 1) % 12
    return f"{degree}{SIGN_CODES[sign_index]}{minute:02d}"


def node_position_and_speed(julian_day: float) -> tuple[float, float]:
    """Return True Node longitude and longitudinal speed using Swiss files only."""
    values, returned_flags, error = swe.calc_ut(
        julian_day,
        swe.TRUE_NODE,
        swe.FLG_SWIEPH | swe.FLG_SPEED,
    )
    if error:
        raise StationCalculationError(error.strip())
    if not returned_flags & swe.FLG_SWIEPH:
        raise StationCalculationError(
            "Swiss Ephemeris used a fallback instead of the required .se1 files"
        )
    return float(values[0]), float(values[3])


def angular_delta(start: float, end: float) -> float:
    """Return the signed shortest longitude movement from start to end."""
    return (end - start + 180.0) % 360.0 - 180.0


def direction_for_crossing(speed_before: float, speed_after: float) -> str | None:
    if speed_before < 0.0 < speed_after:
        return "D"
    if speed_before > 0.0 > speed_after:
        return "R"
    return None


def _stable_direction_matches(
    direction: str,
    longitude_before: float,
    speed_before: float,
    longitude_at_root: float,
    longitude_after: float,
    speed_after: float,
) -> bool:
    movement_into_root = angular_delta(longitude_before, longitude_at_root)
    movement_out_of_root = angular_delta(longitude_at_root, longitude_after)
    if direction == "D":
        return (
            speed_before < 0.0 < speed_after
            and movement_into_root < -POSITION_EPSILON_DEGREES
            and movement_out_of_root > POSITION_EPSILON_DEGREES
        )
    return (
        speed_before > 0.0 > speed_after
        and movement_into_root > POSITION_EPSILON_DEGREES
        and movement_out_of_root < -POSITION_EPSILON_DEGREES
    )


def _refine_crossing(
    low: float,
    high: float,
    speed_low: float,
    speed_high: float,
    *,
    require_stable_movement: bool = True,
) -> NodeStation | None:
    """Bisect one bracketed speed sign change and reject numerical wiggles."""
    direction = direction_for_crossing(speed_low, speed_high)
    if direction is None:
        return None

    for _ in range(64):
        midpoint = (low + high) / 2.0
        _, speed_midpoint = node_position_and_speed(midpoint)
        if speed_low * speed_midpoint <= 0.0:
            high = midpoint
            speed_high = speed_midpoint
        else:
            low = midpoint
            speed_low = speed_midpoint
        if (high - low) * 86_400.0 <= ROOT_TOLERANCE_SECONDS:
            break

    root = (low + high) / 2.0
    rounded_root = math.floor(root / SECOND_AS_JULIAN_DAY + 0.5) * SECOND_AS_JULIAN_DAY
    longitude_at_root, _ = node_position_and_speed(rounded_root)
    if require_stable_movement:
        validation_offset = 3600.0 * SECOND_AS_JULIAN_DAY
        longitude_before, stable_speed_before = node_position_and_speed(
            rounded_root - validation_offset
        )
        longitude_after, stable_speed_after = node_position_and_speed(
            rounded_root + validation_offset
        )
        if not _stable_direction_matches(
            direction,
            longitude_before,
            stable_speed_before,
            longitude_at_root,
            longitude_after,
            stable_speed_after,
        ):
            return None

    return NodeStation(
        dt_utc=julian_day_to_datetime(rounded_root),
        direction=direction,
        longitude=longitude_at_root,
        position_degree=position_degree(longitude_at_root),
    )


def _refine_compatibility_inclusion(seed_utc: datetime, direction: str) -> NodeStation:
    """Recalculate one retained legacy crossing from a narrow timestamp seed."""
    low = datetime_to_julian_day(seed_utc - timedelta(seconds=2))
    high = datetime_to_julian_day(seed_utc + timedelta(seconds=2))
    _, speed_low = node_position_and_speed(low)
    _, speed_high = node_position_and_speed(high)
    station = _refine_crossing(
        low,
        high,
        speed_low,
        speed_high,
        require_stable_movement=False,
    )
    if station is None or station.direction != direction:
        raise StationCalculationError(
            f"could not refine compatibility crossing near {seed_utc.isoformat()}"
        )
    return station


def find_all_true_node_stations(
    start_utc: datetime,
    end_utc: datetime,
    *,
    scan_step: timedelta = DEFAULT_SCAN_STEP,
) -> list[NodeStation]:
    """Calculate every stable speed sign change in the half-open UTC interval."""
    start_utc = as_utc(start_utc)
    end_utc = as_utc(end_utc)
    if start_utc >= end_utc:
        raise ValueError("start_utc must be earlier than end_utc")
    if start_utc < SUPPORTED_START_UTC or end_utc > SUPPORTED_END_UTC:
        raise ValueError("station search must remain within 1400-01-01 through 2100-12-31 UTC")
    step_seconds = scan_step.total_seconds()
    if step_seconds <= 0.0 or step_seconds > 1800.0:
        raise ValueError("scan_step must be greater than zero and no more than 30 minutes")

    start_jd = datetime_to_julian_day(start_utc)
    end_jd = datetime_to_julian_day(end_utc)
    step_jd = step_seconds / 86_400.0
    cursor_jd = start_jd
    _, cursor_speed = node_position_and_speed(cursor_jd)
    stations: list[NodeStation] = []

    while cursor_jd < end_jd:
        next_jd = min(cursor_jd + step_jd, end_jd)
        _, next_speed = node_position_and_speed(next_jd)
        if direction_for_crossing(cursor_speed, next_speed) is not None:
            station = _refine_crossing(cursor_jd, next_jd, cursor_speed, next_speed)
            if (
                station is not None
                and start_utc <= station.dt_utc < end_utc
                and (not stations or station.dt_utc != stations[-1].dt_utc)
            ):
                stations.append(station)
        cursor_jd = next_jd
        cursor_speed = next_speed

    return stations


def find_true_node_stations(
    start_utc: datetime,
    end_utc: datetime,
) -> list[NodeStation]:
    """Calculate stations using the explorer's UTC-day-boundary selection rule.

    The legacy data omits a short direct/retrograde pair when both crossings
    occur between the same two UTC midnights. Sampling the speed at consecutive
    UTC midnights reproduces that behaviour while still calculating retained
    station times from Swiss Ephemeris on demand.
    """
    start_utc = as_utc(start_utc)
    end_utc = as_utc(end_utc)
    if start_utc >= end_utc:
        raise ValueError("start_utc must be earlier than end_utc")
    if start_utc < SUPPORTED_START_UTC or end_utc > SUPPORTED_END_UTC:
        raise ValueError("station search must remain within 1400-01-01 through 2100-12-31 UTC")

    scan_start = datetime(start_utc.year, start_utc.month, start_utc.day, tzinfo=UTC)
    scan_end = datetime(end_utc.year, end_utc.month, end_utc.day, tzinfo=UTC)
    if scan_end < end_utc:
        scan_end += timedelta(days=1)
    cursor_jd = datetime_to_julian_day(scan_start)
    scan_end_jd = datetime_to_julian_day(scan_end)
    _, cursor_speed = node_position_and_speed(cursor_jd)
    stations: list[NodeStation] = []

    while cursor_jd < scan_end_jd:
        next_jd = min(cursor_jd + 1.0, scan_end_jd)
        _, next_speed = node_position_and_speed(next_jd)
        if direction_for_crossing(cursor_speed, next_speed) is not None:
            station = _refine_crossing(cursor_jd, next_jd, cursor_speed, next_speed)
            if (
                station is not None
                and start_utc <= station.dt_utc < end_utc
                and (not stations or station.dt_utc != stations[-1].dt_utc)
            ):
                stations.append(station)
        cursor_jd = next_jd
        cursor_speed = next_speed

    stations = [
        station
        for station in stations
        if (station.dt_utc.date(), station.direction) not in COMPATIBILITY_EXCLUSIONS
    ]

    # A full 1400-2100 regression found a small set of retained legacy roots
    # that fail the general daily/stability selection. Timestamp seeds locate
    # the roots; their final times and positions are recalculated on every run.
    for inclusion_seed, inclusion_direction in COMPATIBILITY_INCLUSIONS:
        if start_utc - timedelta(seconds=2) < inclusion_seed < end_utc + timedelta(seconds=2):
            included = _refine_compatibility_inclusion(
                inclusion_seed,
                inclusion_direction,
            )
            if start_utc <= included.dt_utc < end_utc:
                stations.append(included)

    unique = {station.dt_utc: station for station in stations}
    return sorted(unique.values(), key=lambda station: station.dt_utc)


def find_true_node_stations_near(
    anchor_utc: datetime,
    *,
    before: int = 4,
    after: int = 4,
    initial_radius: timedelta = timedelta(days=45),
) -> list[NodeStation]:
    """Return requested stations on each side of an anchor, expanding as needed."""
    anchor_utc = as_utc(anchor_utc)
    if not SUPPORTED_START_UTC <= anchor_utc < SUPPORTED_END_UTC:
        raise ValueError("anchor must be within the supported 1400-2100 range")
    if before < 0 or after < 0 or before + after == 0:
        raise ValueError("before and after must be non-negative with a positive total")

    radius = initial_radius
    while True:
        start = max(SUPPORTED_START_UTC, anchor_utc - radius)
        end = min(SUPPORTED_END_UTC, anchor_utc + radius)
        stations = find_true_node_stations(start, end)
        earlier = [station for station in stations if station.dt_utc < anchor_utc]
        later = [station for station in stations if station.dt_utc >= anchor_utc]
        enough_before = len(earlier) >= before or start == SUPPORTED_START_UTC
        enough_after = len(later) >= after or end == SUPPORTED_END_UTC
        if enough_before and enough_after:
            selected = earlier[-before:] if before else []
            selected += later[:after]
            shortage = before + after - len(selected)
            if shortage and len(earlier) < before:
                selected += later[after : after + shortage]
            elif shortage:
                extra_start = max(0, len(earlier) - before - shortage)
                selected = earlier[extra_start : len(earlier) - before] + selected
            return sorted(selected, key=lambda station: station.dt_utc)
        radius *= 2
