from datetime import datetime, timedelta, timezone

import pytest

from calculations.cycles import (
    PROGRESSION_FACTORS,
    generate_cycle_events,
    project_station,
    source_anchor_for_target,
)
from calculations.ephemeris import configure_ephemeris
from calculations.node_stations import (
    find_all_true_node_stations,
    find_true_node_stations,
    position_degree,
)


UTC = timezone.utc


@pytest.fixture(scope="module", autouse=True)
def configured_ephemeris():
    configure_ephemeris()


def test_closest_known_station_pair_is_detected():
    stations = find_true_node_stations(
        datetime(2033, 12, 28, 22, tzinfo=UTC),
        datetime(2033, 12, 29, 3, tzinfo=UTC),
    )

    assert [(station.dt_utc, station.direction, station.position_degree) for station in stations] == [
        (datetime(2033, 12, 28, 23, 12, 56, tzinfo=UTC), "D", "7LI37"),
        (datetime(2033, 12, 29, 1, 23, 27, tzinfo=UTC), "R", "7LI37"),
    ]


@pytest.mark.parametrize(
    ("start", "end", "expected"),
    [
        (
            datetime(1449, 11, 16, 8, tzinfo=UTC),
            datetime(1449, 11, 16, 13, tzinfo=UTC),
            [(datetime(1449, 11, 16, 10, 27, 29, tzinfo=UTC), "D", "25AQ20")],
        ),
        (
            datetime(1913, 12, 19, 21, tzinfo=UTC),
            datetime(1913, 12, 20, 2, tzinfo=UTC),
            [(datetime(1913, 12, 19, 23, 46, 53, tzinfo=UTC), "D", "18PI36")],
        ),
        (
            datetime(1620, 10, 20, tzinfo=UTC),
            datetime(1620, 10, 21, tzinfo=UTC),
            [],
        ),
    ],
)
def test_difficult_regression_cases(start, end, expected):
    stations = find_true_node_stations(start, end)

    assert [(station.dt_utc, station.direction, station.position_degree) for station in stations] == expected


def test_position_degree_rolls_minutes_into_the_next_sign():
    assert position_degree(29 + 59.6 / 60) == "0TA00"


def test_search_rejects_steps_that_could_skip_close_pairs():
    with pytest.raises(ValueError, match="30 minutes"):
        find_all_true_node_stations(
            datetime(2000, 1, 1, tzinfo=UTC),
            datetime(2000, 1, 2, tzinfo=UTC),
            scan_step=timedelta(hours=1),
        )


def test_compatibility_search_omits_same_day_minor_pair():
    start = datetime(1400, 1, 13, tzinfo=UTC)
    end = datetime(1400, 1, 14, tzinfo=UTC)

    assert len(find_all_true_node_stations(start, end)) == 2
    assert find_true_node_stations(start, end) == []


def test_compatibility_search_applies_a_legacy_exclusion():
    start = datetime(1489, 4, 1, tzinfo=UTC)
    end = datetime(1489, 4, 3, tzinfo=UTC)

    assert len(find_all_true_node_stations(start, end)) == 2
    assert find_true_node_stations(start, end) == []


@pytest.mark.parametrize("converse", [False, True])
def test_cycle_projection_round_trip(converse):
    reference = datetime(1980, 1, 1, 12, tzinfo=UTC)
    target = datetime(2026, 8, 30, 12, tzinfo=UTC)
    factor = 365.242199074074

    source = source_anchor_for_target(
        reference,
        target,
        factor=factor,
        converse=converse,
    )

    assert abs(
        (project_station(reference, source, factor=factor, converse=converse) - target).total_seconds()
    ) < 0.001


@pytest.mark.parametrize("method", PROGRESSION_FACTORS)
@pytest.mark.parametrize("converse", [False, True])
def test_generate_cycle_events_surrounds_anchor(method, converse):
    reference = datetime(1980, 1, 1, 12, tzinfo=UTC)
    anchor = datetime(2026, 8, 30, 12, tzinfo=UTC)

    events = generate_cycle_events(
        reference,
        anchor,
        method=method,
        converse=converse,
    )

    assert len(events) == 8
    assert events == sorted(events, key=lambda event: event.projected_dt_utc)
    assert len([event for event in events if event.projected_dt_utc < anchor]) == 4
    assert len([event for event in events if event.projected_dt_utc >= anchor]) == 4
