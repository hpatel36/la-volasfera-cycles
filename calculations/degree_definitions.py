"""Load and resolve public-domain symbolic degree definitions."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


DATA_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "la_volasfera_degree_definitions.json"
)


@dataclass(frozen=True)
class DegreeDefinition:
    title: str
    image: str
    interpretation: str


@lru_cache(maxsize=1)
def load_la_volasfera() -> dict[str, DegreeDefinition]:
    """Load and validate the complete 360-degree La Volasfera transcription."""
    raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or len(raw) != 360:
        raise RuntimeError("La Volasfera data must contain exactly 360 degree entries")

    definitions: dict[str, DegreeDefinition] = {}
    for key, entry in raw.items():
        if not isinstance(entry, dict):
            raise RuntimeError(f"Invalid La Volasfera entry: {key}")
        meaning = str(entry.get("meaning", "")).strip()
        title, separator, interpretation = meaning.partition(" - ")
        definitions[str(key).upper()] = DegreeDefinition(
            title=title.strip(),
            image=str(entry.get("description", "")).strip(),
            interpretation=(interpretation if separator else meaning).strip(),
        )
    return definitions


def degree_key(position_degree: str) -> str:
    """Convert a compact zodiac position such as 10CP20 to its degree key."""
    normalized = str(position_degree).strip().upper()
    if len(normalized) < 3:
        raise ValueError(f"invalid zodiac position: {position_degree}")
    return normalized[:-2]


def lookup_la_volasfera(position_degree: str) -> DegreeDefinition:
    """Return the La Volasfera image and interpretation for a station position."""
    key = degree_key(position_degree)
    try:
        return load_la_volasfera()[key]
    except KeyError as error:
        raise ValueError(f"no La Volasfera definition for {position_degree}") from error
