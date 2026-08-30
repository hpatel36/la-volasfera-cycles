"""Compare generated True Node stations with an AstriumLab database."""

from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from calculations.ephemeris import configure_ephemeris  # noqa: E402
from calculations.node_stations import find_true_node_stations  # noqa: E402


UTC = timezone.utc


def expected_rows(database: Path, year: int) -> list[tuple[str, str, str]]:
    connection = sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True)
    try:
        return connection.execute(
            """
            SELECT event_date, event_type, position_degree
            FROM NodeRetro
            WHERE event_date >= ? AND event_date < ?
            ORDER BY event_date
            """,
            (f"{year:04d}-01-01 00:00:00", f"{year + 1:04d}-01-01 00:00:00"),
        ).fetchall()
    finally:
        connection.close()


def generated_rows(year: int) -> list[tuple[str, str, str]]:
    stations = find_true_node_stations(
        datetime(year, 1, 1, tzinfo=UTC),
        datetime(year + 1, 1, 1, tzinfo=UTC),
    )
    return [
        (
            station.dt_utc.strftime("%Y-%m-%d %H:%M:%S"),
            station.direction,
            station.position_degree,
        )
        for station in stations
    ]


def rows_match(
    expected: list[tuple[str, str, str]],
    generated: list[tuple[str, str, str]],
) -> bool:
    if len(expected) != len(generated):
        return False
    for expected_row, generated_row in zip(expected, generated, strict=True):
        expected_dt = datetime.strptime(expected_row[0], "%Y-%m-%d %H:%M:%S")
        generated_dt = datetime.strptime(generated_row[0], "%Y-%m-%d %H:%M:%S")
        if abs((expected_dt - generated_dt).total_seconds()) > 1.0:
            return False
        if expected_row[1:] != generated_row[1:]:
            return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    parser.add_argument("--start-year", type=int, default=1400)
    parser.add_argument("--end-year", type=int, default=2100)
    arguments = parser.parse_args()
    configure_ephemeris()

    expected_count = 0
    generated_count = 0
    mismatched_years: list[int] = []
    for year in range(arguments.start_year, arguments.end_year + 1):
        expected = expected_rows(arguments.database, year)
        generated = generated_rows(year)
        expected_count += len(expected)
        generated_count += len(generated)
        if not rows_match(expected, generated):
            mismatched_years.append(year)
            print(f"Mismatch in {year}: expected {len(expected)}, generated {len(generated)}")
            expected_set = set(expected)
            generated_set = set(generated)
            for row in sorted(expected_set - generated_set)[:5]:
                print(f"  missing: {row}")
            for row in sorted(generated_set - expected_set)[:5]:
                print(f"  extra:   {row}")
        if (year - arguments.start_year + 1) % 25 == 0:
            print(f"Checked through {year}")

    print(f"expected={expected_count}")
    print(f"generated={generated_count}")
    print(f"mismatched_years={len(mismatched_years)}")
    return 1 if mismatched_years else 0


if __name__ == "__main__":
    raise SystemExit(main())
