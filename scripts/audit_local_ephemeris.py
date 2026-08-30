"""Audit the minimal Swiss Ephemeris files needed for True Node stations.

This is a local development audit. It copies candidate ephemeris files to a
temporary directory and checks every NodeRetro row in a read-only reference
database without modifying it.
"""

from __future__ import annotations

import argparse
import math
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import swisseph as swe


FLAGS = swe.FLG_SWIEPH | swe.FLG_SPEED
SECOND = 1.0 / 86_400.0
SIGN_CODES = ("AR", "TA", "GE", "CN", "LE", "VI", "LI", "SC", "SA", "CP", "AQ", "PI")


def julian_day(value: str) -> float:
    parsed = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    hour = parsed.hour + parsed.minute / 60.0 + parsed.second / 3600.0
    return swe.julday(parsed.year, parsed.month, parsed.day, hour, swe.GREG_CAL)


def calculate(jd_ut: float) -> tuple[float, float]:
    values, returned_flags, error = swe.calc_ut(jd_ut, swe.TRUE_NODE, FLAGS)
    if error:
        raise RuntimeError(error)
    if not returned_flags & swe.FLG_SWIEPH:
        raise RuntimeError(f"Swiss files were not used (returned flags: {returned_flags})")
    return float(values[0]), float(values[3])


def position_degree(longitude: float) -> str:
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


def child(ephe_path: Path, database: Path) -> int:
    swe.set_ephe_path(str(ephe_path))
    connection = sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True)
    try:
        rows = connection.execute(
            "SELECT event_date, event_type, position_degree FROM NodeRetro ORDER BY event_date"
        ).fetchall()
    finally:
        connection.close()

    direction_failures: list[tuple[str, str, float, float]] = []
    position_failures: list[tuple[str, str, str]] = []
    for event_date, event_type, expected_position in rows:
        jd_ut = julian_day(event_date)
        longitude, _ = calculate(jd_ut)
        _, speed_before = calculate(jd_ut - SECOND)
        _, speed_after = calculate(jd_ut + SECOND)
        direction_ok = (
            speed_before < 0.0 < speed_after
            if event_type == "D"
            else speed_before > 0.0 > speed_after
        )
        if not direction_ok:
            _, speed_before = calculate(jd_ut - 2 * SECOND)
            _, speed_after = calculate(jd_ut + 2 * SECOND)
            direction_ok = (
                speed_before < 0.0 < speed_after
                if event_type == "D"
                else speed_before > 0.0 > speed_after
            )
        if not direction_ok:
            direction_failures.append((event_date, event_type, speed_before, speed_after))
        actual_position = position_degree(longitude)
        if actual_position != expected_position:
            position_failures.append((event_date, expected_position, actual_position))

    print(f"rows={len(rows)}")
    print(f"direction_failures={len(direction_failures)}")
    print(f"position_failures={len(position_failures)}")
    for failure in direction_failures[:5]:
        print(f"direction_failure={failure}")
    for failure in position_failures[:5]:
        print(f"position_failure={failure}")
    return 0 if not direction_failures and not position_failures else 1


def parent(source: Path, database: Path, candidates: tuple[str, ...]) -> int:
    with tempfile.TemporaryDirectory(prefix="lavolasfera-ephe-audit-") as temporary:
        ephe_path = Path(temporary)
        for filename in candidates:
            shutil.copy2(source / filename, ephe_path / filename)
        command = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--child",
            "--ephe-path",
            str(ephe_path),
            "--database",
            str(database),
        ]
        child_environment = os.environ.copy()
        child_environment.pop("SE_EPHE_PATH", None)
        completed = subprocess.run(command, check=False, env=child_environment)
        print(f"files={','.join(candidates)}")
        print(f"bytes={sum((source / name).stat().st_size for name in candidates)}")
        return completed.returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--files", nargs="+", default=("semo_12.se1", "semo_18.se1"))
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--ephe-path", type=Path)
    arguments = parser.parse_args()
    if arguments.child:
        return child(arguments.ephe_path, arguments.database)
    if arguments.source is None:
        parser.error("--source is required")
    return parent(arguments.source, arguments.database, tuple(arguments.files))


if __name__ == "__main__":
    raise SystemExit(main())
